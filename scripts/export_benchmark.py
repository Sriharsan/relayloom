"""Turn docs/benchmark-results.json (written by `python -m relayloom.ap.benchmark`) into the file the site reads.

Usage: python scripts/export_benchmark.py OUT_JSON
Every value comes from the results file. Nothing is typed in here.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"correct": "Correct delivery", "short": "Short delivery", "over_billed_price": "Price above the order",
         "duplicate_bill": "Duplicate bill", "split_delivery": "Split delivery",
         "split_delivery_short": "Split delivery that ends short", "hidden_text_injection": "Hidden text in the bill"}


def rupees(value: float) -> str:
    return "₹ " + format(value, ",.2f")


def main():
    out = Path(sys.argv[1])
    r = json.loads((ROOT / "docs" / "benchmark-results.json").read_text(encoding="utf-8"))
    a, b = r["pipeline_a"], r["pipeline_b"]
    bad, good = a["should_hold"], a["should_enter"]
    rows = [
        {"metric": "Bad bills caught", "paperworkOnly": f"{a['errors_caught']} of {bad}",
         "paperworkPlusGoods": f"{b['errors_caught']} of {bad}", "basis": "short, over priced, duplicate and short split bills"},
        {"metric": "Wrong payments made", "paperworkOnly": rupees(a["wrong_payments_made_inr"]),
         "paperworkPlusGoods": rupees(b["wrong_payments_made_inr"]), "basis": "demo rupees"},
        {"metric": "Wrong payments avoided", "paperworkOnly": rupees(a["wrong_payments_avoided_inr"]),
         "paperworkPlusGoods": rupees(b["wrong_payments_avoided_inr"]), "basis": "demo rupees"},
        {"metric": "Clean bills held by mistake", "paperworkOnly": f"{a['false_holds']} of {good}",
         "paperworkPlusGoods": f"{b['false_holds']} of {good}", "basis": "good bills held"},
        {"metric": "Cost of the goods check", "paperworkOnly": "none",
         "paperworkPlusGoods": f"{r['sam_seconds_per_delivery']} s per delivery",
         "basis": "SAM 3.1 inference on a laptop CPU, recorded"},
    ]
    scenarios = []
    for key, c in r["by_category"].items():
        if c["should_enter"]:
            right_a, right_b, rule = c["a_entered"], c["b_entered"], "should be entered"
        else:
            right_a, right_b, rule = c["deliveries"] - c["a_entered"], c["deliveries"] - c["b_entered"], "should be held"
        scenarios.append({"scenario": NAMES.get(key, key), "deliveries": c["deliveries"], "rule": rule,
                          "paperworkOnly": right_a, "plusGoods": right_b})
    sam = r["sam"]
    note = (f"SAM 3.1 counted {sam['exactly_right']} of {sam['photos']} unique photos exactly right. "
            "Bill values come from the generator, and findings are written by code from the evidence.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"setSize": a["deliveries"], "rows": rows, "perScenario": scenarios, "note": note}, indent=1,
                              ensure_ascii=False), encoding="utf-8")
    print(f"benchmark exported: {a['deliveries']} deliveries, caught {a['errors_caught']} vs {b['errors_caught']} of {bad}")


if __name__ == "__main__":
    main()
