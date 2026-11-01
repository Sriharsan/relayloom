"""Relayloom accounts payable: the local app. Loopback only.

python -m relayloom.ap                      rehearsal: recorded Meta model outputs, built in ledger
python -m relayloom.ap --live               Muse Glimmer and SAM 3.1 on this machine, ERPNext from .env
Mix with --reader, --counter and --ledger. The screen and every receipt say which ran.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlsplit

from .ledger import ERPNextLedger, LocalLedger
from .models import GlimmerClient, RecordedGlimmer, SamCounter
from .pipeline import Network, Workbench
from .policy import Refused, load_policy
from .portal import BrowserDisputer, Portal
from .receipts import ReceiptChain, Signer, verify

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "ap"
FIXTURES = ROOT / "fixtures"
MAX_BODY = 4096


def load_env(path: Path = ROOT / ".env"):
    """Read KEY=value lines into the environment without printing anything."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() and not name.startswith("#") and value.strip():
            os.environ.setdefault(name.strip(), value.strip())


def build(args) -> tuple[Workbench, dict]:
    data = json.loads((FIXTURES / "data.json").read_text(encoding="utf-8"))
    run_dir = Path(args.data) / time.strftime("run-%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    policy = load_policy()
    signer = Signer(Path(args.data) / "receipt-signing.key")
    chain = ReceiptChain(run_dir / "receipts.jsonl", signer, policy.hash)
    if args.reader == "live":
        reader = GlimmerClient(os.environ.get("GLIMMER_URL", "http://127.0.0.1:8082/v1"),
                               os.environ.get("GLIMMER_ROUTE", "Muse Glimmer 30B Q4_K_M, llama.cpp CPU, this machine"))
    else:
        reader = RecordedGlimmer()
    counter = SamCounter(os.environ.get("RELAYLOOM_SAM_PYTHON", ""), os.environ.get("RELAYLOOM_SAM_WEIGHTS", ""),
                         os.environ.get("SAM_ROUTE", "SAM 3.1 (sam3.1_multiplex.pt), Ultralytics, CPU, this laptop"),
                         live=args.counter == "live")
    if args.ledger == "erpnext":
        def erp():
            return ERPNextLedger(os.environ.get("ERPNEXT_URL", "http://localhost:8080"), os.environ["ERPNEXT_API_KEY"],
                                 os.environ["ERPNEXT_API_SECRET"], os.environ.get("ERPNEXT_COMPANY", data["company"]["name"]))
        ledger, checker = erp(), erp()  # the Checker uses its own client and its own requests
        data["tax_account"] = os.environ.get("ERPNEXT_TAX_ACCOUNT", "")
    else:
        ledger = LocalLedger(run_dir / "local-ledger.sqlite3")
        ledger.seed(data["suppliers"], data["purchase_orders"], data["history_invoices"])
        checker = LocalLedger(run_dir / "local-ledger.sqlite3")
    portal_server = Portal(args.portal_port).start()
    disputer = BrowserDisputer(f"http://127.0.0.1:{args.portal_port}", run_dir / "media")
    network = Network(ledger, checker, disputer)
    bench = Workbench(policy, ledger, checker, chain, reader, counter, network, FIXTURES, data, portal=disputer)
    run = {"started": time.strftime("%Y-%m-%d %H:%M %z"), "dir": run_dir.name, "ledger": ledger.name,
           "reader": "Muse Glimmer (live)" if args.reader == "live" else "Muse Glimmer (recorded outputs)",
           "counter": "SAM 3.1 (live)" if args.counter == "live" else "SAM 3.1 (recorded outputs)",
           "mode": "live" if args.reader == args.counter == "live" else "rehearsal" if args.reader == args.counter == "recorded" else "mixed",
           "public_key": signer.public_key, "policy_hash": policy.hash}
    (run_dir / "run.json").write_text(json.dumps(run, indent=1), encoding="utf-8")
    bench.portal_server = portal_server
    bench.run_dir = run_dir
    return bench, run


class App(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, bench: Workbench, run: dict):
        if address[0] != "127.0.0.1":
            raise ValueError("bind to loopback only")
        self.bench, self.run = bench, run
        super().__init__(address, Handler)

    def state(self) -> dict:
        bench = self.bench
        cases = [case.view() for case in bench.cases.values()]
        counts = {k: sum(1 for c in cases if c["state"] in v) for k, v in {
            "entered_checked": ("entered_checked",), "held_for_owner": ("held_for_owner",),
            "held_offline": ("held_offline",), "disputes_sent": ("dispute_sent",),
            "other": ("failed", "readback_failed", "closed_by_owner")}.items()}
        gateway_log = ROOT / "data" / "gateway.jsonl"
        gateway = [json.loads(l) for l in gateway_log.read_text(encoding="utf-8").splitlines()[-50:]] if gateway_log.exists() else []
        masks = [{"case": c["id"], "kinds": [m["kind"] for m in c["masks"]]} for c in cases if c["masks"]]
        return {"run": self.run, "online": bench.network.online, "cases": cases, "counts": counts,
                "policy": {"hash": bench.policy.hash, "operations": {k: v["level"] for k, v in bench.policy.data["operations"].items()},
                           "limits": bench.policy.limits, "egress": bench.policy.data["egress"]},
                "boundary": {"gateway_log": gateway, "masks": masks, "model_calls_outside": 0 if not gateway else
                             sum(1 for g in gateway if g.get("decision") == "allowed")}}


class Handler(BaseHTTPRequestHandler):
    server_version = "Relayloom"
    sys_version = ""

    def log_message(self, format, *args):
        return

    def common(self, status, kind, length):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; "
                         "img-src 'self'; connect-src 'self'; font-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()

    def json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.common(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def file(self, path: Path):
        if not path.is_file():
            return self.json(404, {"error": "not found"})
        body = path.read_bytes()
        self.common(200, mimetypes.guess_type(path.name)[0] or "application/octet-stream", len(body))
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        app = self.server
        if url.path == "/api/state":
            return self.json(200, app.state())
        if url.path == "/api/receipts":
            case = parse_qs(url.query).get("case", [None])[0]
            receipts = app.bench.chain.read(case)
            ok, problems = verify(app.bench.chain.read(), app.run["public_key"])
            return self.json(200, {"receipts": receipts, "verified": ok, "problems": problems,
                                   "public_key": app.run["public_key"]})
        if url.path.startswith("/media/"):
            name = Path(url.path[7:]).name
            for folder in (app.bench.run_dir / "media", FIXTURES / "photos", FIXTURES / "recorded" / "sam"):
                if (folder / name).is_file():
                    return self.file(folder / name)
            return self.json(404, {"error": "not found"})
        name = "index.html" if url.path in ("/", "") else Path(url.path).name
        return self.file(WEB / name)

    def do_POST(self):
        app = self.server
        origin = self.headers.get("Origin", "")
        if self.headers.get("X-Relayloom") != "1" or (origin and urlsplit(origin).hostname != "127.0.0.1"):
            return self.json(403, {"error": "same origin requests only"})
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY:
            return self.json(413, {"error": "too large"})
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self.json(400, {"error": "bad json"})
        bench = app.bench
        try:
            if self.path == "/api/batch":
                names = body.get("cases") or [c["case"] for c in bench.data["cases"]]
                records = [c for c in bench.data["cases"] if c["case"] in names and c["case"] not in bench.cases]
                bench.submit(records)
                return self.json(200, {"started": [r["case"] for r in records]})
            if self.path == "/api/decide":
                threading.Thread(target=self.safe, args=(bench.decide, body.get("case", ""), body.get("decision", ""), "Owner"),
                                 daemon=True).start()
                return self.json(202, {"ok": True})
            if self.path == "/api/network":
                if body.get("online"):
                    threading.Thread(target=self.safe, args=(bench.reconnect,), daemon=True).start()
                else:
                    bench.network.cut()
                return self.json(200, {"online": bool(body.get("online"))})
        except (Refused, KeyError) as error:
            return self.json(409, {"error": str(error)})
        return self.json(404, {"error": "not found"})

    @staticmethod
    def safe(function, *args):
        try:
            function(*args)
        except Exception as error:  # Shown on the case through its receipts; the server keeps running.
            print(f"action refused: {type(error).__name__}: {error}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--portal-port", type=int, default=8890)
    parser.add_argument("--live", action="store_true", help="Glimmer and SAM 3.1 live on this machine, ERPNext ledger")
    parser.add_argument("--reader", choices=("live", "recorded"), default="recorded")
    parser.add_argument("--counter", choices=("live", "recorded"), default="recorded")
    parser.add_argument("--ledger", choices=("local", "erpnext"), default="local")
    parser.add_argument("--data", default=str(ROOT / "data" / "ap"))
    parser.add_argument("--batch", action="store_true", help="start the five demo cases on launch")
    args = parser.parse_args()
    if args.live:
        args.reader, args.counter, args.ledger = "live", "live", "erpnext"
    load_env()
    bench, run = build(args)
    server = App(("127.0.0.1", args.port), bench, run)
    print(f"Relayloom accounts payable, {run['mode']} mode: http://127.0.0.1:{args.port}")
    print(f"Reader: {run['reader']}. Counter: {run['counter']}. Ledger: {run['ledger']}. Synthetic data only.")
    if args.batch:
        bench.submit(bench.data["cases"])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        bench.portal_server.shutdown()


if __name__ == "__main__":
    main()
