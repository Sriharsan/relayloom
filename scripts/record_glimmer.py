"""Read the synthetic bills with Muse Glimmer on this machine and save each real output.

Usage: python scripts/record_glimmer.py [BILL_NO ...] [--disputes]
Needs llama-server with Muse Glimmer on GLIMMER_URL (default http://127.0.0.1:8081/v1).
Saved files are labelled with route, model, timings and date, and replayed only as "recorded".
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relayloom.ap.masking import mask  # noqa: E402
from relayloom.ap.models import DISPUTE_SYSTEM, READER_SYSTEM, GlimmerClient, parse_json  # noqa: E402
from relayloom.ap.schema import BILL_SCHEMA, validate_bill  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "recorded" / "glimmer"
ROUTE = os.environ.get("GLIMMER_ROUTE", "Muse Glimmer 30B Q4_K_M, llama.cpp b12020 CPU, this laptop")


def save(kind, key, reply, extra):
    OUT.mkdir(parents=True, exist_ok=True)
    record = {"recorded_at": time.strftime("%Y-%m-%d %H:%M %z"), "machine": platform.processor() or platform.machine(),
              "reply": reply, **extra}
    (OUT / f"{kind}-{key}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
    client = GlimmerClient(os.environ.get("GLIMMER_URL", "http://127.0.0.1:8081/v1"), ROUTE)
    for case in data["cases"]:
        if args and case["bill_no"] not in args:
            continue
        masked, _ = mask((ROOT / "fixtures" / case["bill_text"]).read_text(encoding="utf-8"))
        if "--disputes" not in sys.argv:
            reply = client.chat(READER_SYSTEM, "Bill text:\n<<<\n" + masked + "\n>>>", BILL_SCHEMA)
            reply["route"] = ROUTE
            try:
                bill = validate_bill(parse_json(reply["content"]))
                verdict = "valid" if bill == validate_bill(case["expected_bill"]) else "valid, differs from fixture"
            except ValueError as error:
                verdict = f"invalid: {error}"
            save("read", case["bill_no"], reply, {"input_sha256": hashlib.sha256(masked.encode()).hexdigest(),
                                                  "schema_check": verdict})
            print(f"{case['bill_no']}: {reply['seconds']} s, {reply['usage']}, {verdict}", flush=True)
    if "--disputes" in sys.argv:
        facts_by_bill = json.loads((ROOT / "fixtures" / "dispute_facts.json").read_text(encoding="utf-8"))
        for bill_no, facts in facts_by_bill.items():
            if args and bill_no not in args:
                continue
            reply = client.chat(DISPUTE_SYSTEM, "Facts:\n" + json.dumps(facts, indent=1), None, max_tokens=1024)
            reply["route"] = ROUTE
            save("dispute", bill_no, reply, {"facts_sha256": hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest()})
            print(f"dispute {bill_no}: {reply['seconds']} s, {reply['usage']}", flush=True)


if __name__ == "__main__":
    main()
