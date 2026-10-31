"""Write the dispute facts for the mismatch cases, as the Disputer builds them from the PO, bill and count.

The counts are the delivered quantities in the synthetic photos. A recorded dispute is replayed only
when a run produces exactly these facts.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relayloom.ap.matcher import match  # noqa: E402
from relayloom.ap.pipeline import dispute_facts  # noqa: E402
from relayloom.ap.policy import load_policy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
limits = load_policy().limits
facts = {}
for case in data["cases"]:
    po = next(p for p in data["purchase_orders"] if p["po_number"] == case["po_number"])
    result = match(po, case["expected_bill"], {case["count_item"]: case["delivered_in_photo"]}, limits)
    if not result["matched"]:
        supplier = next(s for s in data["suppliers"] if s["id"] == case["supplier_id"])["name"]
        facts[case["bill_no"]] = dispute_facts(supplier, case["bill_no"], case["po_number"], result)
(ROOT / "fixtures" / "dispute_facts.json").write_text(json.dumps(facts, indent=1), encoding="utf-8")
print("dispute facts for", ", ".join(facts))
