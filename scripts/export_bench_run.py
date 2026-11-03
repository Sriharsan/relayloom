"""Run the demo cases on the bench and export what the site replays.

Usage: python scripts/export_bench_run.py OUT_JSON

The agents, matcher, Investigator, policy, ledger (built in), Checker and signed receipts all run for real.
Bill values come from the bill records. Counts come from SAM 3.1 where a recorded SAM 3.1 run exists for that
photo (fixtures/recorded/sam), otherwise from the delivery record; every count says which.
"""
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.alerts import AlertHub  # noqa: E402
from relayloom.ap.ledger import LocalLedger  # noqa: E402
from relayloom.ap.pipeline import Network, Workbench  # noqa: E402
from relayloom.ap.policy import load_policy  # noqa: E402
from relayloom.ap.receipts import ReceiptChain, Signer, verify  # noqa: E402
from relayloom.ap.schema import validate_bill  # noqa: E402

FIXTURES = ROOT / "fixtures"
SAM = FIXTURES / "recorded" / "sam"
DATA = json.loads((FIXTURES / "data.json").read_text(encoding="utf-8"))
TRUE = {p["id"]: p["true_count"] for e in DATA["receiving_events"] for p in e["photos"]}
DEMO = ["match", "short", "price", "injection", "duplicate", "split"]


class RecordReader:
    route = "bench"

    def read_bill(self, masked_text, key=""):
        case = next(c for c in DATA["cases"] if c["bill_no"] == key)
        return {"bill": validate_bill(json.loads(json.dumps(case["expected_bill"]))), "model": "bill record",
                "route": "bench", "seconds": 0.0, "response_id": f"bench-{key}"}

    def draft_dispute(self, facts, key=""):
        text = (f"Bill {facts['bill_no']} on {facts['po_number']}: {facts['problems'][0]} "
                "Please send a credit note for the difference.")
        return {"text": text, "model": "template", "route": "bench", "seconds": 0.0, "response_id": f"bench-d-{key}"}


class SamOrRecordCounter:
    def count(self, photo, prompt, key):
        path = SAM / f"{key}__{prompt.replace(' ', '-')}.json"
        if path.exists():
            result = json.loads(path.read_text(encoding="utf-8"))["result"]
            return {"count": result["count"], "prompt": prompt, "model": "SAM 3.1", "route": result["route"],
                    "infer_seconds": result["infer_seconds"], "overlay": result["overlay"]}
        return {"count": TRUE[key], "prompt": prompt, "model": "delivery record", "route": "bench",
                "infer_seconds": 0.0, "overlay": ""}


class BenchPortal:
    def __init__(self):
        self.sent = []

    def submit(self, case):
        self.sent.append(case.id)
        return {"reference": f"DSP-{len(self.sent):04d}", "filled_by": "code", "seconds": 0.0}


def main():
    out = Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        policy = load_policy()
        signer = Signer(root / "key")
        chain = ReceiptChain(root / "receipts.jsonl", signer, policy.hash)
        ledger = LocalLedger(root / "ledger.sqlite3")
        ledger.seed(DATA["suppliers"], DATA["purchase_orders"], DATA["history_invoices"])
        bench = Workbench(policy, ledger, ledger, chain, RecordReader(), SamOrRecordCounter(), Network(ledger),
                          FIXTURES, DATA, portal=BenchPortal())
        hub = AlertHub()
        bench.casefile_dir = root / "casefiles"
        bench.notify = lambda kind, title, body, case: hub.publish(kind, title, body, case)
        records = [c for c in DATA["cases"] if c["case"] in DEMO]
        started = time.time()
        cases = bench.run_batch(records)
        decisions = {"short": "approve", "price": "reject", "duplicate": "approve"}
        for case in cases:
            if case.id in decisions and case.state == "held_for_owner":
                bench.decide(case.id, decisions[case.id], "Owner")
        # Network cut mid batch: the link drops after the first invoice is accepted, then comes back.
        cut_bench = Workbench(policy, ledger, ledger, chain, RecordReader(), SamOrRecordCounter(), Network(ledger),
                              FIXTURES, DATA, portal=BenchPortal())
        cut_bench.casefile_dir = root / "casefiles"
        cut_bench.notify = lambda kind, title, body, case: hub.publish(kind, title, body, case)
        cut_bench.after_create = lambda case: cut_bench.network.cut() if cut_bench.network.online else None
        cut_bench.pool._max_workers = 1
        cut_records = [c for c in DATA["cases"] if c["case"].startswith("netcut")]
        cut_cases = cut_bench.run_batch(cut_records)
        held_views = [case.view() for case in cut_cases]
        in_books_while_cut = sum(ledger.count_invoices(c.supplier_id, c.bill_no) for c in cut_cases)
        cut_bench.after_create = None
        cut_bench.reconnect()
        cut_bench.reconnect()
        in_books_after = sum(ledger.count_invoices(c.supplier_id, c.bill_no) for c in cut_cases)
        netcut = {"held": [{"id": v["id"], "bill_no": v["bill_no"], "state": v["state"], "status": v["status"],
                            "read": bool(v["bill"])} for v in held_views],
                  "in_books_while_cut": in_books_while_cut, "in_books_after_reconnect": in_books_after,
                  "after": [{"id": c.id, "bill_no": c.bill_no, "state": c.state, "status": c.status}
                            for c in cut_cases]}
        receipts = chain.read()
        casefiles = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((root / "casefiles").glob("*.json"))}
        patterns = bench.supplier_patterns()
        supplier_files = {sid: bench.supplier_file(sid) for sid in sorted({c.supplier_id for c in cases})}
        ok, problems = verify(receipts, signer.public_key)
        export = {
            "ran_at": time.strftime("%Y-%m-%d %H:%M %z"),
            "seconds": round(time.time() - started, 2),
            "policy_hash": policy.hash,
            "public_key": signer.public_key,
            "receipts_verified": ok,
            "receipt_problems": problems,
            "suppliers": {s["id"]: s["name"] for s in DATA["suppliers"]},
            "cases": [{**case.view(), "masked_text": ""} for case in cases],  # the bill text is not shown on the site
            "netcut": netcut,
            "casefiles": casefiles,
            "alerts": hub.items,
            "supplier_files": supplier_files,
            "supplier_patterns": patterns,
            "receipts": receipts,
        }
        ledger.db.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(export, indent=1, default=str), encoding="utf-8")
    states = ", ".join(f"{c['id']}={c['state']}" for c in export["cases"])
    print(f"{len(export['cases'])} cases in {export['seconds']} s; receipts verified: {ok}; {states}")
    print(f"network cut: {[c['state'] for c in netcut['held']]} with {netcut['in_books_while_cut']} in the books, "
          f"after reconnect {[c['state'] for c in netcut['after']]} with {netcut['in_books_after_reconnect']}")


if __name__ == "__main__":
    main()
