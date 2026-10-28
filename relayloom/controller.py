"""SQLite state and bounded execution. Rehearsal is the default worker."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import threading
import time

ROLES = ("product", "engineering", "support")
LABELS = {"product": "Product", "engineering": "Engineering", "support": "Support"}
CONFIG = "rehearsal-v1:scope=draft-only:no-tools"


class Rejected(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(packed(value).encode()).hexdigest()


def text(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise Rejected(f"{label} must contain 1–{maximum} characters.")
    return value.strip()


def intent_fields(body):
    days = body.get("refund_days")
    if type(days) is not int or not 0 <= days <= 365:
        raise Rejected("Refund days must be an integer from 0 to 365.")
    return {"brief": text(body.get("brief"), "Goal", 4000),
            "audience": text(body.get("audience"), "Audience", 200), "refund_days": days}


def scoped_inputs(role, intent, dependencies=None):
    """The same role-scoped inputs drive both cache keys and provider prompts."""
    if role == "product":
        return {key: intent[key] for key in ("brief", "audience")}
    elif role == "engineering":
        return {"refund_days": intent["refund_days"]}
    return {"intent": intent, "dependencies": dependencies}


def task_input(role, intent, dependencies=None, config=CONFIG):
    # The complete configuration and draft-only authority are part of the key.
    return digest({"role": role, "inputs": scoped_inputs(role, intent, dependencies), "config": config})


def rehearsal_worker(role, intent, dependencies):
    """Synthetic outputs exercise real scheduling; these are not AI responses."""
    time.sleep({"product": 0.15, "engineering": 1.2, "support": 0.1}[role])
    if role == "product":
        return {"summary": f"Prepare a clear response for {intent['audience']}: {intent['brief']}",
                "audience": intent["audience"], "brief": intent["brief"]}
    if role == "engineering":
        return {"summary": f"Use an inclusive {intent['refund_days']}-day refund window. No external system is changed.",
                "refund_days": intent["refund_days"], "boundary": "draft-only"}
    return {"summary": f"For {intent['audience']}, explain the {intent['refund_days']}-day refund policy and the shared goal.",
            "refund_days": intent["refund_days"], "audience": intent["audience"],
            "dependencies": {key: digest(value) for key, value in dependencies.items()}}


def validate_output(role, result, intent, dependencies):
    if not isinstance(result, dict) or len(packed(result)) > 12000:
        raise Rejected("Specialist returned malformed or oversized evidence.")
    text(result.get("summary"), "Specialist summary", 6000)
    if role == "product" and (result.get("audience") != intent["audience"] or result.get("brief") != intent["brief"]):
        raise Rejected("Product output does not match its assigned inputs.")
    if role in ("engineering", "support") and (type(result.get("refund_days")) is not int or result["refund_days"] != intent["refund_days"]):
        raise Rejected("Refund policy does not match current intent.")
    if role == "engineering" and result.get("boundary") != "draft-only":
        raise Rejected("Engineering output exceeds its draft-only boundary.")
    if role == "support" and (result.get("audience") != intent["audience"] or result.get("dependencies") != {key: digest(value) for key, value in dependencies.items()}):
        raise Rejected("Support output is not bound to its current dependencies.")
    return result


class Controller:
    def __init__(self, path, worker=rehearsal_worker):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.worker = worker
        self.mode = getattr(worker, "mode", "rehearsal")
        self.configuration = getattr(worker, "configuration", CONFIG)
        if hasattr(worker, "ledger") and worker.ledger.path.resolve() == self.path:
            raise ValueError("Use separate workroom and Meta ledger database paths.")
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="relayloom")
        self.lock = threading.Lock()
        self.running = set()
        self.wake = set()
        self.scheduler_threads = set()
        self.closed = threading.Event()
        with self.db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS rooms(id TEXT PRIMARY KEY,name TEXT NOT NULL,
                  revision INTEGER NOT NULL,intent TEXT NOT NULL,publish INTEGER NOT NULL DEFAULT 0,seq INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS members(id TEXT PRIMARY KEY,room TEXT NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,member TEXT NOT NULL,csrf TEXT NOT NULL,expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS invites(hash TEXT PRIMARY KEY,room TEXT NOT NULL,role TEXT NOT NULL,expires REAL NOT NULL,used INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS tasks(room TEXT NOT NULL,revision INTEGER NOT NULL,role TEXT NOT NULL,
                  state TEXT NOT NULL,input_hash TEXT NOT NULL,origin INTEGER,output TEXT,reason TEXT NOT NULL,
                  PRIMARY KEY(room,revision,role));
                CREATE TABLE IF NOT EXISTS events(room TEXT NOT NULL,seq INTEGER NOT NULL,type TEXT NOT NULL,message TEXT NOT NULL,created REAL NOT NULL,
                  PRIMARY KEY(room,seq));
                CREATE TABLE IF NOT EXISTS artifacts(room TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL,
                  checks TEXT NOT NULL,PRIMARY KEY(room,revision));
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            """)
            policy = packed({"mode": self.mode, "configuration": self.configuration})
            saved = db.execute("SELECT value FROM settings WHERE key='worker'").fetchone()
            legacy_rooms = db.execute("SELECT count(*) FROM rooms").fetchone()[0]
            if (saved and saved[0] != policy) or (not saved and legacy_rooms and self.mode != "rehearsal"):
                raise ValueError("This database belongs to a different worker mode/configuration. Use a separate reviewed database.")
            db.execute("INSERT OR IGNORE INTO settings VALUES('worker',?)", (policy,))
            interrupted = db.execute("SELECT DISTINCT room FROM tasks WHERE state='RUNNING'").fetchall()
            db.execute("UPDATE tasks SET state='FAILED',reason='Server restarted; review and explicitly run again.' WHERE state='RUNNING'")
            for row in interrupted:
                self.event(db, row[0], "interrupted", "Interrupted work needs an explicit restart. No automatic retry occurred.")

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def event(self, db, room, kind, message):
        db.execute("UPDATE rooms SET seq=seq+1 WHERE id=?", (room,))
        seq = db.execute("SELECT seq FROM rooms WHERE id=?", (room,)).fetchone()[0]
        db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (room, seq, kind, message, time.time()))

    def issue_session(self, db, member):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (digest(token), member, csrf, time.time() + 8 * 3600))
        return token

    def authenticate(self, db, token, csrf=None):
        row = db.execute("""SELECT m.*,s.csrf,s.hash AS session_hash FROM sessions s JOIN members m ON m.id=s.member
          WHERE s.hash=? AND s.expires>? AND m.active=1""", (digest(token or ""), time.time())).fetchone()
        if row is None:
            raise Rejected("Sign in to this workroom first.", 401)
        if csrf is not None and not secrets.compare_digest(str(csrf), row["csrf"]):
            raise Rejected("Refresh the page before trying this action.", 403)
        return row

    @staticmethod
    def authority(member, owner=False):
        if member["role"] not in (("owner",) if owner else ("owner", "editor")):
            raise Rejected("Your role cannot perform this action.", 403)

    @staticmethod
    def current(db, member, revision):
        row = db.execute("SELECT * FROM rooms WHERE id=?", (member["room"],)).fetchone()
        if type(revision) is not int or row["revision"] != revision:
            raise Rejected("The intent changed. Review the latest revision and try again.", 409)
        return row

    def new_tasks(self, db, room, revision, intent, previous=None):
        for role in ROLES:
            key = task_input(role, intent, config=self.configuration)
            old = None
            if previous and role != "support":
                old = db.execute("SELECT * FROM tasks WHERE room=? AND revision=? AND role=? AND state IN ('COMPLETE','REUSED') AND input_hash=?", (room, previous, role, key)).fetchone()
            db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?)", (
                room, revision, role, "REUSED" if old else "WAITING", key,
                old["origin"] if old else None, old["output"] if old else None,
                "Relevant inputs and draft authority still match." if old else ("Waiting for Product and Engineering." if role == "support" else "Ready to run with the shared intent.")))

    def create(self, body):
        name = text(body.get("name"), "Workroom name", 100)
        display = text(body.get("display_name"), "Your name", 80)
        intent = {"brief": text(body.get("brief"), "Goal", 4000), "refund_days": 30, "audience": "Customers"}
        if hasattr(self.worker, "validate_intent"):
            self.worker.validate_intent(intent)
        room, member = secrets.token_hex(16), secrets.token_hex(16)
        with self.db() as db:
            # Local rehearsal is bounded rather than an unauthenticated hosting service.
            if db.execute("SELECT count(*) FROM rooms").fetchone()[0] >= 100:
                raise Rejected("This local rehearsal has reached its 100-workroom limit.", 429)
            db.execute("INSERT INTO rooms(id,name,revision,intent) VALUES(?,?,1,?)", (room, name, packed(intent)))
            db.execute("INSERT INTO members(id,room,name,role) VALUES(?,?,?,'owner')", (member, room, display))
            self.new_tasks(db, room, 1, intent)
            self.event(db, room, "created", "Workroom created in local rehearsal mode." if self.mode == "rehearsal" else "Synthetic-only Meta mode configured. Calls occur only when specialists are run.")
            return self.issue_session(db, member)

    def join(self, body):
        display = text(body.get("display_name"), "Your name", 80)
        invite = text(body.get("invite"), "Invite", 160)
        with self.db() as db:
            row = db.execute("SELECT * FROM invites WHERE hash=? AND used=0 AND expires>?", (digest(invite), time.time())).fetchone()
            if row is None:
                raise Rejected("That invite is invalid, expired or already used.", 403)
            member = secrets.token_hex(16)
            db.execute("UPDATE invites SET used=1 WHERE hash=?", (row["hash"],))
            db.execute("INSERT INTO members(id,room,name,role) VALUES(?,?,?,?)", (member, row["room"], display, row["role"]))
            self.event(db, row["room"], "joined", f"A {row['role']} joined the workroom.")
            return self.issue_session(db, member)

    def session(self, token):
        with self.db() as db:
            try:
                member = self.authenticate(db, token)
            except Rejected:
                return {"signed_in": False}
            return {"signed_in": True, "csrf": member["csrf"], "member": {"name": member["name"], "role": member["role"]}}

    def snapshot(self, token):
        with self.db() as db:
            member = self.authenticate(db, token)
            room = db.execute("SELECT * FROM rooms WHERE id=?", (member["room"],)).fetchone()
            tasks = db.execute("SELECT * FROM tasks WHERE room=? AND revision=?", (room["id"], room["revision"])).fetchall()
            task_map = {row["role"]: row for row in tasks}
            artifact = db.execute("SELECT * FROM artifacts WHERE room=? ORDER BY revision DESC LIMIT 1", (room["id"],)).fetchone()
            return {
                "room": {"id": room["id"], "name": room["name"], "revision": room["revision"], "intent": json.loads(room["intent"]), "permission": {"publish": bool(room["publish"])}, "mode": self.mode},
                "member": {"name": member["name"], "role": member["role"]},
                "tasks": [{"role": role, "label": LABELS[role], "state": task_map[role]["state"], "reason": task_map[role]["reason"], "origin_revision": task_map[role]["origin"], "summary": json.loads(task_map[role]["output"])["summary"] if task_map[role]["output"] else None} for role in ROLES],
                "events": [{"seq": row["seq"], "type": row["type"], "message": row["message"], "created_at": row["created"]} for row in reversed(db.execute("SELECT * FROM events WHERE room=? ORDER BY seq DESC LIMIT 100", (room["id"],)).fetchall())],
                "artifact": {"revision": artifact["revision"], "checks": json.loads(artifact["checks"]), "payload": json.loads(artifact["payload"])} if artifact else None,
                "metrics": {**(self.worker.metrics(room["id"]) if hasattr(self.worker, "metrics") else {"model_calls": 0}), "outputs_reused": db.execute("SELECT count(*) FROM tasks WHERE room=? AND state='REUSED'", (room["id"],)).fetchone()[0], "artifacts_published": db.execute("SELECT count(*) FROM artifacts WHERE room=?", (room["id"],)).fetchone()[0]}}

    def mutate(self, token, csrf, action, body):
        launch = None
        with self.db() as db:
            member = self.authenticate(db, token, csrf if csrf is not None else "")
            room_id = member["room"]
            if action == "logout":
                db.execute("DELETE FROM sessions WHERE hash=?", (member["session_hash"],))
                return {"ok": True}
            self.authority(member, owner=action in ("invites", "permission", "publish"))
            if action == "invites":
                role = body.get("role")
                if role not in ("viewer", "editor"):
                    raise Rejected("Choose viewer or editor access.")
                if db.execute("SELECT count(*) FROM invites WHERE room=? AND used=0 AND expires>?", (room_id, time.time())).fetchone()[0] >= 20:
                    raise Rejected("Use or expire existing invites before creating more.", 429)
                invite = secrets.token_urlsafe(32)
                expires = time.time() + 1800
                db.execute("INSERT INTO invites(hash,room,role,expires) VALUES(?,?,?,?)", (digest(invite), room_id, role, expires))
                return {"invite": invite, "expires": expires}
            room = self.current(db, member, body.get("revision"))
            revision = room["revision"]
            if action == "intent":
                intent = intent_fields(body)
                if hasattr(self.worker, "validate_intent"):
                    self.worker.validate_intent(intent)
                if packed(intent) == room["intent"]:
                    return {"ok": True, "revision": revision}
                if revision >= 1000:
                    raise Rejected("This local rehearsal has reached its revision limit.", 429)
                db.execute("UPDATE rooms SET revision=revision+1,intent=?,publish=0 WHERE id=?", (packed(intent), room_id))
                db.execute("UPDATE tasks SET state='SUPERSEDED',reason='Intent changed while work was running.' WHERE room=? AND revision=? AND state='RUNNING'", (room_id, revision))
                self.new_tasks(db, room_id, revision + 1, intent, previous=revision)
                self.event(db, room_id, "intent_changed", f"{member['name']} advanced intent to revision {revision + 1}; publish permission reset.")
            elif action == "permission":
                if type(body.get("publish")) is not bool:
                    raise Rejected("Publication permission must be true or false.")
                db.execute("UPDATE rooms SET publish=? WHERE id=?", (int(body["publish"]), room_id))
                self.event(db, room_id, "permission", f"{member['name']} allowed publication for this revision." if body["publish"] else f"{member['name']} revoked publication permission.")
            elif action == "run":
                db.execute("UPDATE tasks SET state='WAITING',reason='Explicitly retried after failure.' WHERE room=? AND revision=? AND state='FAILED'", (room_id, revision))
                launch = room_id
            elif action == "publish":
                if not room["publish"]:
                    raise Rejected("The owner must allow publication for this revision.", 403)
                previous = db.execute("SELECT * FROM artifacts WHERE room=? AND revision=?", (room_id, revision)).fetchone()
                if previous:
                    return {"ok": True, "replayed": True}
                tasks = {row["role"]: row for row in db.execute("SELECT * FROM tasks WHERE room=? AND revision=?", (room_id, revision))}
                if any(tasks[role]["state"] not in ("COMPLETE", "REUSED") for role in ROLES):
                    raise Rejected("All current specialists must complete before publication.", 409)
                intent = json.loads(room["intent"])
                outputs = {role: json.loads(tasks[role]["output"]) for role in ROLES}
                for role in ROLES:
                    dependencies = {key: outputs[key] for key in ROLES[:2]} if role == "support" else {}
                    if tasks[role]["input_hash"] != task_input(role, intent, dependencies, self.configuration):
                        raise Rejected("Output provenance does not match current intent.", 409)
                    validate_output(role, outputs[role], intent, dependencies)
                payload = {"intent": intent, "specialists": outputs, "scope": "local-artifact-only", "mode": self.mode}
                checks = {"current_revision": True, "inputs_and_dependencies": True, "owner_permission": True, "draft_only_scope": True}
                db.execute("INSERT INTO artifacts VALUES(?,?,?,?)", (room_id, revision, packed(payload), packed(checks)))
                self.event(db, room_id, "published", f"{member['name']} published a verified local artifact for revision {revision}.")
            else:
                raise Rejected("Unknown action.", 404)
        if launch:
            self.start(launch)
        return {"ok": True}

    def start(self, room):
        with self.lock:
            if self.closed.is_set():
                return
            if room in self.running:
                self.wake.add(room)
                return
            self.running.add(room)
            worker = threading.Thread(target=self._run, args=(room,), daemon=True, name="relayloom-scheduler")
            self.scheduler_threads.add(worker)
            worker.start()

    def _run(self, room):
        try:
            while not self.closed.is_set():
                futures = []
                with self.db() as db:
                    current = db.execute("SELECT * FROM rooms WHERE id=?", (room,)).fetchone()
                    revision, intent = current["revision"], json.loads(current["intent"])
                    tasks = {row["role"]: row for row in db.execute("SELECT * FROM tasks WHERE room=? AND revision=?", (room, revision))}
                    for role in ROLES:
                        if tasks[role]["state"] != "WAITING":
                            continue
                        dependencies = {}
                        if role == "support":
                            if not all(tasks[key]["state"] in ("COMPLETE", "REUSED") for key in ROLES[:2]):
                                continue
                            dependencies = {key: json.loads(tasks[key]["output"]) for key in ROLES[:2]}
                        key = task_input(role, intent, dependencies, self.configuration)
                        db.execute("UPDATE tasks SET state='RUNNING',input_hash=?,reason='Working with current inputs.' WHERE room=? AND revision=? AND role=?", (key, room, revision, role))
                        self.event(db, room, "started", f"{LABELS[role]} started on revision {revision}.")
                        if hasattr(self.worker, "execute"):
                            future = self.executor.submit(self.worker.execute, f"{room}:{revision}:{role}", room, role, intent, dependencies)
                        else:
                            future = self.executor.submit(self.worker, role, intent, dependencies)
                        futures.append((role, intent, dependencies, future))
                if not futures:
                    return
                for role, assigned_intent, dependencies, future in futures:
                    try:
                        result = validate_output(role, future.result(), assigned_intent, dependencies)
                        error = None
                    except Exception:
                        result, error = None, "Specialist failed or returned evidence outside its assigned contract."
                    with self.db() as db:
                        current = db.execute("SELECT revision FROM rooms WHERE id=?", (room,)).fetchone()[0]
                        if current != revision:
                            self.event(db, room, "stale_discarded", f"Late {LABELS[role]} result from revision {revision} was discarded.")
                        else:
                            db.execute("UPDATE tasks SET state=?,output=?,origin=?,reason=? WHERE room=? AND revision=? AND role=? AND state='RUNNING'", ("FAILED" if error else "COMPLETE", packed(result) if result else None, revision if result else None, error or "Assigned inputs and output contract verified.", room, revision, role))
                            self.event(db, room, "failed" if error else "completed", f"{LABELS[role]} {'failed validation' if error else 'completed'} on revision {revision}.")
        finally:
            with self.lock:
                self.running.discard(room)
                self.scheduler_threads.discard(threading.current_thread())
                again = room in self.wake
                self.wake.discard(room)
            if again:
                self.start(room)

    def close(self):
        self.closed.set()
        with self.lock:
            workers = list(self.scheduler_threads)
        for worker in workers:
            worker.join()
        self.executor.shutdown(wait=True, cancel_futures=True)
