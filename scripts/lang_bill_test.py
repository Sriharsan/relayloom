"""Read a Hindi and a Tamil supplier bill with Muse Glimmer on this machine and compare every field with the known answer.

Usage: python scripts/lang_bill_test.py            (needs Muse Glimmer on GLIMMER_URL, default http://127.0.0.1:8085/v1)
Writes docs/LANGUAGE_BILL_RESULT.md. The bills are fixtures/bills_lang/*.txt, written for this test with Latin digits and
supplier, item and order codes, which is how Indian invoices usually print them.
"""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.masking import mask  # noqa: E402
from relayloom.ap.models import GlimmerClient  # noqa: E402

TRUTH = {"supplier_id": "SUP-CALDER", "po_number": "PO-2003", "bill_date": "2026-11-03", "tax_inr": 1062.0, "total_inr": 6962.0,
         "line": {"item_code": "CARTON-HD", "qty": 50, "rate_inr": 118.0, "amount_inr": 5900.0}}
BILLS = [("Hindi", "hindi-CAL-0991.txt", "CAL-0991"), ("Tamil", "tamil-CAL-0992.txt", "CAL-0992")]


def compare(bill, bill_no):
    line = bill["lines"][0] if bill.get("lines") else {}
    checks = {"supplier_id": bill.get("supplier_id") == TRUTH["supplier_id"], "bill_no": bill.get("bill_no") == bill_no,
              "po_number": bill.get("po_number") == TRUTH["po_number"], "bill_date": bill.get("bill_date") == TRUTH["bill_date"],
              "one line": len(bill.get("lines", [])) == 1, "item_code": line.get("item_code") == TRUTH["line"]["item_code"],
              "qty": line.get("qty") == TRUTH["line"]["qty"], "rate": line.get("rate_inr") == TRUTH["line"]["rate_inr"],
              "amount": line.get("amount_inr") == TRUTH["line"]["amount_inr"], "tax": bill.get("tax_inr") == TRUTH["tax_inr"],
              "total": bill.get("total_inr") == TRUTH["total_inr"]}
    return checks


def main():
    client = GlimmerClient(os.environ.get("GLIMMER_URL", "http://127.0.0.1:8085/v1"), "Muse Glimmer 30B Q4_K_M, llama.cpp CPU, this laptop", timeout=2400)
    rows = []
    for language, name, bill_no in BILLS:
        text = (ROOT / "fixtures" / "bills_lang" / name).read_text(encoding="utf-8")
        masked, records = mask(text)
        started = time.perf_counter()
        try:
            reply = client.read_bill(masked)
            bill, error, seconds = reply["bill"], "", reply["seconds"]
            checks = compare(bill, bill_no)
        except Exception as exc:  # a real failure is a result too
            bill, checks, seconds, error = None, {}, round(time.perf_counter() - started, 1), f"{type(exc).__name__}: {str(exc)[:200]}"
        rows.append({"language": language, "file": name, "masked": [r["kind"] for r in records], "seconds": seconds, "error": error, "bill": bill, "checks": checks})
        print(language, seconds, "s", error or f"{sum(checks.values())} of {len(checks)} fields correct", flush=True)
    lines = ["# A Hindi and a Tamil bill through Muse Glimmer", "",
             f"Run {time.strftime('%Y-%m-%d %H:%M %z')} on this laptop's CPU, Muse Glimmer 30B Q4_K_M, the same reader and schema as English bills. "
             "The bills are test fixtures written for this check, with Latin digits and printed supplier, item and order codes. Private numbers were masked first.", "",
             "| Language | Seconds | Fields correct | Wrong or missing |", "| --- | --- | --- | --- |"]
    for r in rows:
        wrong = [k for k, v in r["checks"].items() if not v]
        lines.append(f"| {r['language']} | {r['seconds']} | {sum(r['checks'].values())} of {len(r['checks'])} | {', '.join(wrong) or ('none' if not r['error'] else r['error'])} |")
    lines += ["", "```json", json.dumps({r["language"]: r["bill"] for r in rows}, ensure_ascii=False, indent=1), "```", ""]
    (ROOT / "docs" / "LANGUAGE_BILL_RESULT.md").write_text("\n".join(lines), encoding="utf-8")
    json.dump(rows, open(ROOT / "docs" / "language_bill_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
