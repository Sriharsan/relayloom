"""Record real Muse Glimmer outputs on this machine for the demo cases and save them with route, model and timings.

Usage: python scripts/record_glimmer.py [--reads] [--findings] [--disputes] [BILL_NO ...]
Needs llama-server with Muse Glimmer on GLIMMER_URL (default http://127.0.0.1:8082/v1) and the SAM counts already
recorded (scripts/record_sam.py --world demo --alt). Reading a bill takes 5 to 12 minutes per bill on a laptop CPU.
Findings and disputes are written from the exact evidence and facts the pipeline builds, captured first by a dry run
that uses no model, so a recorded output replays only when the inputs are identical.
Saved outputs are replayed later only as "recorded".
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relayloom.ap.ledger import LocalLedger  # noqa: E402
from relayloom.ap.masking import mask  # noqa: E402
from relayloom.ap.models import (BILL_SCHEMA, DISPUTE_SYSTEM, FINDING_SCHEMA, FINDING_SYSTEM, READER_SYSTEM,  # noqa: E402
                                 GlimmerClient, SamCounter, parse_json)
from relayloom.ap.pipeline import Network, Workbench  # noqa: E402
from relayloom.ap.policy import load_policy  # noqa: E402
from relayloom.ap.receipts import ReceiptChain, Signer  # noqa: E402
from relayloom.ap.schema import validate_bill  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "recorded" / "glimmer"
ROUTE = os.environ.get("GLIMMER_ROUTE", "Muse Glimmer 30B Q4_K_M, llama.cpp b12020 CPU, this laptop")
MISMATCH = ("short", "price", "duplicate")


class Capture:
    """Dry run reader: returns the true bill, remembers what the pipeline would send to Muse Glimmer."""

    writes_findings = True
    route = "capture"

    def __init__(self, cases):
        self.cases, self.findings, self.facts = cases, {}, {}

    def read_bill(self, masked_text, key=""):
        bill = next(c for c in self.cases if c["bill_no"] == key)["expected_bill"]
        return {"bill": validate_bill(json.loads(json.dumps(bill))), "model": "none", "route": "capture", "seconds": 0, "response_id": ""}

    def write_finding(self, evidence_text, key=""):
        self.findings[key] = evidence_text
        raise RuntimeError("capture only")

    def draft_dispute(self, facts, key=""):
        self.facts[key] = facts
        return {"text": "capture", "model": "none", "route": "capture", "seconds": 0, "response_id": ""}


def capture(data, case_name):
    work = Path(tempfile.mkdtemp())
    policy = load_policy()
    chain = ReceiptChain(work / "r.jsonl", Signer(work / "k"), policy.hash)
    ledger = LocalLedger(work / "l.sqlite3")
    ledger.seed(data["suppliers"], data["purchase_orders"], data["history_invoices"])
    reader = Capture(data["cases"])
    counter = SamCounter(live=False)
    bench = Workbench(policy, ledger, ledger, chain, reader, counter, Network(ledger), ROOT / "fixtures", data)
    bench.run_batch([c for c in data["cases"] if c["case"] == case_name])
    return reader


def save(kind, key, reply, extra):
    OUT.mkdir(parents=True, exist_ok=True)
    record = {"recorded_at": time.strftime("%Y-%m-%d %H:%M %z"), "machine": platform.processor() or platform.machine(),
              "reply": {**reply, "route": ROUTE}, **extra}
    (OUT / f"{kind}-{key}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    everything = not flags
    data = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
    client = GlimmerClient(os.environ.get("GLIMMER_URL", "http://127.0.0.1:8082/v1"), ROUTE)
    if everything or "--reads" in flags:
        for case in data["cases"]:
            if only and case["bill_no"] not in only:
                continue
            if (OUT / f"read-{case['bill_no']}.json").exists() and not only:
                continue
            masked, _ = mask((ROOT / "fixtures" / case["bill_text"]).read_text(encoding="utf-8"))
            reply = client.chat(READER_SYSTEM, "Bill text:\n<<<\n" + masked + "\n>>>", BILL_SCHEMA)
            try:
                bill = validate_bill(parse_json(reply["content"]))
                verdict = "valid" if bill == validate_bill(case["expected_bill"]) else "valid, differs from the true bill"
            except ValueError as error:
                verdict = f"invalid: {error}"
            save("read", case["bill_no"], reply, {"input_sha256": hashlib.sha256(masked.encode()).hexdigest(), "schema_check": verdict})
            print(f"read {case['bill_no']}: {reply['seconds']} s, {reply['usage']}, {verdict}", flush=True)
    for name in MISMATCH:
        case = next(c for c in data["cases"] if c["case"] == name)
        if only and case["bill_no"] not in only:
            continue
        seen = capture(data, name)
        key = case["bill_no"]
        if (everything or "--findings" in flags) and key in seen.findings:
            text = seen.findings[key]
            reply = client.chat(FINDING_SYSTEM, "Evidence:\n" + text, FINDING_SCHEMA, max_tokens=1500)
            save("finding", key, reply, {"input_sha256": hashlib.sha256(text.encode()).hexdigest()})
            print(f"finding {key}: {reply['seconds']} s, {reply['usage']}", flush=True)
        if (everything or "--disputes" in flags) and key in seen.facts:
            facts = seen.facts[key]
            reply = client.chat(DISPUTE_SYSTEM, "Facts:\n" + json.dumps(facts, indent=1), None, max_tokens=1024)
            save("dispute", key, reply, {"facts_sha256": hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest()})
            print(f"dispute {key}: {reply['seconds']} s, {reply['usage']}", flush=True)


if __name__ == "__main__":
    main()
