import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from relayloom.controller import Controller, Rejected
from relayloom.server import LocalServer


def quick_worker(role, intent, dependencies):
    # Use the same output contract, without delay in tests that do not measure concurrency.
    if role == "product":
        return {"summary": "Product evidence", "audience": intent["audience"], "brief": intent["brief"]}
    if role == "engineering":
        return {"summary": "Engineering evidence", "refund_days": intent["refund_days"], "boundary": "draft-only"}
    from relayloom.controller import digest
    return {"summary": "Support evidence", "refund_days": intent["refund_days"], "audience": intent["audience"],
            "dependencies": {key: digest(value) for key, value in dependencies.items()}}


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.controller = Controller(Path(self.folder.name) / "test.sqlite3", worker=quick_worker)
        self.owner = self.controller.create({"name": "Synthetic launch", "display_name": "Owner", "brief": "Prepare the release policy"})
        self.csrf = self.controller.session(self.owner)["csrf"]

    def tearDown(self):
        self.controller.close()
        self.folder.cleanup()

    def mutate(self, action, **body):
        return self.controller.mutate(self.owner, self.csrf, action, body)

    def settle(self, token=None):
        token = token or self.owner
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state = self.controller.snapshot(token)
            if all(task["state"] in ("COMPLETE", "REUSED", "FAILED") for task in state["tasks"]):
                return state
            time.sleep(0.01)
        self.fail("Specialists did not settle")

    def member(self, role):
        invite = self.mutate("invites", role=role)["invite"]
        token = self.controller.join({"display_name": role, "invite": invite})
        return token, self.controller.session(token)["csrf"]

    def test_sessions_scoped_and_logout_revokes(self):
        other = self.controller.create({"name": "Another room", "display_name": "Other", "brief": "Other goal"})
        first, second = self.controller.snapshot(self.owner), self.controller.snapshot(other)
        self.assertNotEqual(first["room"]["id"], second["room"]["id"])
        self.assertEqual([event["seq"] for event in second["events"]], [1])
        self.mutate("logout")
        self.assertFalse(self.controller.session(self.owner)["signed_in"])
        with self.assertRaises(Rejected):
            self.controller.snapshot(self.owner)
        self.assertTrue(self.controller.session(other)["signed_in"])

    def test_csrf_and_viewer_cannot_mutate(self):
        viewer, csrf = self.member("viewer")
        self.assertEqual(self.controller.snapshot(viewer)["room"]["name"], "Synthetic launch")
        for action, body in (("run", {"revision": 1}), ("invites", {"role": "editor"}), ("permission", {"revision": 1, "publish": True})):
            with self.assertRaises(Rejected) as caught:
                self.controller.mutate(viewer, csrf, action, body)
            self.assertEqual(caught.exception.status, 403)
        with self.assertRaises(Rejected):
            self.controller.mutate(self.owner, "wrong", "run", {"revision": 1})
        with self.assertRaises(Rejected):
            self.controller.mutate(self.owner, None, "run", {"revision": 1})

    def test_editor_shared_change_and_current_membership_revocation(self):
        editor, csrf = self.member("editor")
        self.controller.mutate(editor, csrf, "intent", {"revision": 1, "brief": "Editor's revision", "audience": "Members", "refund_days": 14})
        owner_state = self.controller.snapshot(self.owner)
        self.assertEqual(owner_state["room"]["revision"], 2)
        self.assertEqual(owner_state["room"]["intent"]["brief"], "Editor's revision")
        with self.assertRaises(Rejected):
            self.controller.mutate(editor, csrf, "permission", {"revision": 2, "publish": True})
        with self.controller.db() as db:
            db.execute("UPDATE members SET active=0 WHERE role='editor'")
        with self.assertRaises(Rejected):
            self.controller.snapshot(editor)
        self.assertTrue(self.controller.session(self.owner)["signed_in"])

    def test_concurrent_publication_produces_one_artifact(self):
        from concurrent.futures import ThreadPoolExecutor
        self.mutate("run", revision=1)
        self.settle()
        self.mutate("permission", revision=1, publish=True)
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.mutate("publish", revision=1), range(6)))
        self.assertEqual(sum(not value.get("replayed", False) for value in results), 1)
        self.assertEqual(self.controller.snapshot(self.owner)["metrics"]["artifacts_published"], 1)

    def test_invites_one_use_and_cannot_escalate(self):
        invite = self.mutate("invites", role="editor")["invite"]
        editor = self.controller.join({"display_name": "Editor", "invite": invite, "role": "owner"})
        self.assertEqual(self.controller.session(editor)["member"]["role"], "editor")
        with self.assertRaises(Rejected):
            self.controller.join({"display_name": "Replay", "invite": invite})
        with self.assertRaises(Rejected):
            self.mutate("invites", role="owner")

    def test_expired_invite_is_rejected(self):
        invite = self.mutate("invites", role="viewer")["invite"]
        with self.controller.db() as db:
            db.execute("UPDATE invites SET expires=0")
        with self.assertRaises(Rejected):
            self.controller.join({"display_name": "Late", "invite": invite})

    def test_revision_compare_and_swap_and_validation(self):
        self.mutate("intent", revision=1, brief="Changed", audience="New customers", refund_days=14)
        with self.assertRaises(Rejected) as caught:
            self.mutate("intent", revision=1, brief="Stale", audience="Everyone", refund_days=30)
        self.assertEqual(caught.exception.status, 409)
        for bad in (True, -1, 366, 1.5, "30"):
            with self.assertRaises(Rejected):
                self.mutate("intent", revision=2, brief="Goal", audience="Customers", refund_days=bad)

    def test_parallel_ready_work_and_waiting_without_worker_calls(self):
        gate = threading.Event()
        both_started = threading.Event()
        calls, lock = [], threading.Lock()
        def blocked(role, intent, dependencies):
            with lock:
                calls.append(role)
                if set(calls) >= {"product", "engineering"}:
                    both_started.set()
            if role != "support":
                gate.wait(3)
            return quick_worker(role, intent, dependencies)
        self.controller.worker = blocked
        self.mutate("run", revision=1)
        self.assertTrue(both_started.wait(2), "Independent specialists did not start together")
        self.assertEqual(set(calls), {"product", "engineering"})
        self.assertEqual(self.controller.snapshot(self.owner)["tasks"][2]["state"], "WAITING")
        for _ in range(4):
            self.mutate("run", revision=1)
        self.assertEqual(len(calls), 2, "Duplicate run requests repeated work")
        gate.set()
        self.assertTrue(all(task["state"] == "COMPLETE" for task in self.settle()["tasks"]))
        self.assertEqual(calls.count("support"), 1)
        self.assertEqual(self.controller.snapshot(self.owner)["metrics"]["model_calls"], 0)

    def test_selective_reuse_and_idempotent_current_publication(self):
        self.mutate("run", revision=1)
        self.settle()
        self.mutate("permission", revision=1, publish=True)
        self.mutate("publish", revision=1)
        self.assertTrue(self.mutate("publish", revision=1)["replayed"])
        state = self.controller.snapshot(self.owner)
        self.mutate("intent", revision=1, **{**state["room"]["intent"], "refund_days": 14})
        state = self.controller.snapshot(self.owner)
        self.assertEqual(state["tasks"][0]["state"], "REUSED")
        self.assertEqual(state["tasks"][0]["origin_revision"], 1)
        self.assertEqual(state["tasks"][1]["state"], "WAITING")
        self.assertFalse(state["room"]["permission"]["publish"])
        with self.assertRaises(Rejected):
            self.mutate("publish", revision=1)
        with self.assertRaises(Rejected):
            self.mutate("publish", revision=2)
        self.mutate("run", revision=2)
        self.settle()
        self.mutate("permission", revision=2, publish=True)
        self.mutate("publish", revision=2)
        state = self.controller.snapshot(self.owner)
        self.assertEqual(state["artifact"]["payload"]["specialists"]["support"]["refund_days"], 14)
        self.assertEqual(state["metrics"]["artifacts_published"], 2)

    def test_changed_audience_invalidates_product(self):
        self.mutate("run", revision=1)
        self.settle()
        state = self.controller.snapshot(self.owner)
        self.mutate("intent", revision=1, **{**state["room"]["intent"], "audience": "Partners"})
        tasks = self.controller.snapshot(self.owner)["tasks"]
        self.assertNotEqual(tasks[0]["state"], "REUSED")
        self.assertNotEqual(tasks[0]["origin_revision"], 1)
        self.assertEqual(tasks[1]["state"], "REUSED")
        self.assertNotEqual(tasks[2]["state"], "REUSED")

    def test_late_outputs_are_discarded_after_revision_change(self):
        started, gate = threading.Event(), threading.Event()
        def delayed(role, intent, dependencies):
            if intent["refund_days"] == 30:
                started.set()
                gate.wait(3)
            return quick_worker(role, intent, dependencies)
        self.controller.worker = delayed
        self.mutate("run", revision=1)
        self.assertTrue(started.wait(2))
        self.mutate("intent", revision=1, brief="Revised", audience="Members", refund_days=7)
        gate.set()
        state = self.settle()
        self.assertEqual(state["room"]["revision"], 2)
        self.assertTrue(any(event["type"] == "stale_discarded" for event in state["events"]))
        self.assertTrue(all(task["origin_revision"] == 2 for task in state["tasks"]))

    def test_malformed_worker_fails_without_publication(self):
        self.controller.worker = lambda *args: {"summary": "Looks done", "refund_days": 999}
        self.mutate("run", revision=1)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            state = self.controller.snapshot(self.owner)
            if any(task["state"] == "FAILED" for task in state["tasks"]):
                break
            time.sleep(.01)
        self.assertTrue(any(task["state"] == "FAILED" for task in state["tasks"]))
        self.mutate("permission", revision=1, publish=True)
        with self.assertRaises(Rejected):
            self.mutate("publish", revision=1)

    def test_output_tampering_fails_provenance_at_publication(self):
        self.mutate("run", revision=1)
        self.settle()
        self.mutate("permission", revision=1, publish=True)
        with self.controller.db() as db:
            db.execute("UPDATE tasks SET input_hash='wrong' WHERE role='engineering'")
        with self.assertRaises(Rejected):
            self.mutate("publish", revision=1)

    def test_restart_preserves_session_artifact_and_marks_interruption(self):
        self.mutate("run", revision=1)
        self.settle()
        self.mutate("permission", revision=1, publish=True)
        self.mutate("publish", revision=1)
        self.controller.close()
        with self.controller.db() as db:
            db.execute("UPDATE tasks SET state='RUNNING' WHERE role='support'")
        self.controller = Controller(self.controller.path, worker=quick_worker)
        state = self.controller.snapshot(self.owner)
        self.assertEqual(state["tasks"][2]["state"], "FAILED")
        self.assertEqual(state["artifact"]["revision"], 1)
        self.assertTrue(self.controller.session(self.owner)["signed_in"])


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.controller = Controller(Path(self.folder.name) / "http.sqlite3", worker=quick_worker)
        self.server = LocalServer(("127.0.0.1", 0), self.controller)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.controller.close()
        self.folder.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        values = {"Content-Type": "application/json", **(headers or {})}
        connection.request(method, path, json.dumps(body) if body is not None else None, values)
        response = connection.getresponse()
        content = response.read()
        result = (response.status, dict(response.getheaders()), content)
        connection.close()
        return result

    def test_real_http_sessions_csrf_headers_and_foreign_origin(self):
        status, headers, _ = self.request("POST", "/api/rooms", {"name": "HTTP room", "display_name": "Owner", "brief": "Synthetic goal"})
        self.assertEqual(status, 201)
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        self.assertIn("HttpOnly; SameSite=Strict", headers["Set-Cookie"])
        status, _, data = self.request("GET", "/api/session", headers={"Cookie": cookie})
        csrf = json.loads(data)["csrf"]
        self.assertEqual(status, 200)
        self.assertEqual(self.request("GET", "/api/state")[0], 401)
        self.assertEqual(self.request("POST", "/api/run", {"revision": 1}, {"Cookie": cookie})[0], 403)
        auth = {"Cookie": cookie, "X-Relayloom-CSRF": csrf}
        self.assertEqual(self.request("POST", "/api/run", {"revision": 1}, auth)[0], 200)
        self.assertEqual(self.request("POST", "/api/run", {"revision": 1}, {**auth, "Origin": "https://attacker.invalid"})[0], 403)
        self.assertEqual(self.request("GET", "/api/state", headers={**auth, "Host": "attacker.invalid"})[0], 403)
        status, headers, _ = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])

    def test_json_limits_and_no_file_traversal(self):
        self.assertEqual(self.request("GET", "/../README.md")[0], 404)
        self.assertEqual(self.request("POST", "/api/rooms", {"brief": "x" * 9000})[0], 413)
        self.assertEqual(self.request("POST", "/api/rooms", [1, 2])[0], 400)
        self.assertEqual(self.request("POST", "/api/rooms", {}, {"Content-Type": "text/plain"})[0], 415)


if __name__ == "__main__":
    unittest.main()
