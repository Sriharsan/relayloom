"""Benchmark on a synthetic set built by us: about 30 deliveries with known answers, two pipelines.

python -m relayloom.ap.benchmark [--counter live|recorded] [--out docs]

Pipeline A, paperwork only: read the bill, match it to the purchase order (quantity left on the order, rate, maths),
enter it if it matches. Pipeline B, paperwork plus goods: also count every delivery photo with SAM 3.1 (duplicate
photos removed, all receiving events on the order added up), match against what was received, and run the
Investigator on every mismatch. Both use the same guards (masking, hidden text, payment details from the supplier
master). The known answers come from how each delivery was built, never from a model.

The Reader step is not re-run for each delivery: bills here come from the generator's own structured bill, so that
the benchmark tests the checks and not the 5 to 12 minutes per bill that Muse Glimmer needs on this CPU. Muse Glimmer's
readings of the demo bills are in docs/RESULTS.md. SAM 3.1 counts are real; with --counter recorded they are replayed
from earlier real runs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time

from .ledger import LocalLedger
from .models import SamCounter
from .pipeline import Network, Workbench
from .policy import load_policy
from .receipts import ReceiptChain, Signer, verify

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"
ENTERED = ("entered_checked",)


class GeneratorBills:
    """Stands in for the Reader in the benchmark: returns the delivery's structured bill. No model is used."""

    route = "generator bill (no model read this bill)"

    def __init__(self, deliveries):
        self.by_bill = {d["bill_no"]: d for d in deliveries}

    def read_bill(self, masked_text, key=""):
        return {"bill": json.loads(json.dumps(self.by_bill[key]["expected_bill"])), "model": "none",
                "route": self.route, "seconds": 0.0, "response_id": ""}

    def draft_dispute(self, facts, key=""):
        return {"text": f"Bill {facts['bill_no']}: " + "; ".join(facts["problems"]), "model": "none",
                "route": "template", "seconds": 0.0, "response_id": ""}


def run_pipeline(name, goods, world, counter, workdir):
    policy = load_policy()
    signer = Signer(workdir / f"{name}.key")
    chain = ReceiptChain(workdir / f"{name}-receipts.jsonl", signer, policy.hash)
    ledger = LocalLedger(workdir / f"{name}-ledger.sqlite3")
    ledger.seed(world["suppliers"], world["purchase_orders"], world["history_invoices"])
    bench = Workbench(policy, ledger, ledger, chain, GeneratorBills(world["deliveries"]), counter, Network(ledger),
                      FIXTURES, world, goods=goods)
    rows = []
    for delivery in world["deliveries"]:
        started = time.perf_counter()
        [case] = bench.run_batch([{**delivery, "case": delivery["id"]}])
        wall = round(time.perf_counter() - started, 2)
        entered = case.state in ENTERED
        rows.append({"id": delivery["id"], "category": delivery["category"], "bill_no": delivery["bill_no"],
                     "total_inr": delivery["expected_bill"]["total_inr"], "should_enter": delivery["truth"]["should_enter"],
                     "loss_if_entered_inr": delivery["truth"]["loss_if_entered_inr"], "entered": entered,
                     "state": case.state, "status": case.status, "wall_seconds": wall,
                     "counted": case.counter.get("total") if goods else None,
                     "proposal": case.proposal["action"] if case.proposal else "",
                     "finding_verified": bool(case.investigation and case.investigation["finding"]["verified"]),
                     "sam_seconds": case.counter.get("seconds") if goods else None,
                     "investigation_seconds": case.steps["investigate"].get("seconds")})
    ok, problems = verify(chain.read(), signer.public_key)
    ledger.db.close()
    return rows, {"receipts": len(chain.read()), "verified": ok, "problems": problems}


def score(rows):
    wrong = [r for r in rows if r["entered"] and not r["should_enter"]]
    caught = [r for r in rows if not r["entered"] and not r["should_enter"]]
    false_holds = [r for r in rows if not r["entered"] and r["should_enter"]]
    good = [r for r in rows if r["should_enter"]]
    bad = [r for r in rows if not r["should_enter"]]
    return {"deliveries": len(rows), "should_enter": len(good), "should_hold": len(bad),
            "errors_caught": len(caught), "errors_missed": len(wrong),
            "wrong_payments_made_inr": round(sum(r["loss_if_entered_inr"] for r in wrong), 2),
            "wrong_payments_avoided_inr": round(sum(r["loss_if_entered_inr"] for r in caught), 2),
            "false_holds": len(false_holds), "correctly_entered": len([r for r in good if r["entered"]]),
            "mean_seconds_per_case": round(sum(r["wall_seconds"] for r in rows) / len(rows), 2),
            "total_seconds": round(sum(r["wall_seconds"] for r in rows), 1)}


def by_category(rows_a, rows_b):
    out = {}
    for a, b in zip(rows_a, rows_b):
        entry = out.setdefault(a["category"], {"deliveries": 0, "should_enter": a["should_enter"], "a_entered": 0, "b_entered": 0})
        entry["deliveries"] += 1
        entry["a_entered"] += a["entered"]
        entry["b_entered"] += b["entered"]
    return out


def sam_accuracy(world, counter):
    """Photo level: how many of the unique photos SAM 3.1 counted exactly right, from the cached real counts."""
    right, total, wrong = 0, 0, []
    from .receiving import Receiving
    receiving = Receiving(world, counter, FIXTURES)
    for event in world["receiving_events"]:
        result = receiving.count_event(event["id"])
        truth = {p["id"]: p["true_count"] for p in event["photos"]}
        for row in result["photos"]:
            if row["counted"]:
                total += 1
                if row["count"] == truth[row["photo"]]:
                    right += 1
                else:
                    wrong.append({"photo": row["photo"], "counted": row["count"], "true": truth[row["photo"]]})
    return {"photos": total, "exactly_right": right, "wrong": wrong}


def write_markdown(result, path: Path):
    a, b = result["pipeline_a"], result["pipeline_b"]
    lines = [
        "# Benchmark", "",
        "**Synthetic set built by us.** Every delivery, bill, photo and earlier invoice is invented and rendered by "
        "`scripts/make_fixtures.py`. The known answers come from how each delivery was built. These results say how the "
        "checks behave on this set. They are not a claim about any real company or industry.", "",
        f"Run on {result['date']}. Command: `python -m relayloom.ap.benchmark`. Machine: {result['machine']}. "
        f"Counter: {result['counter_mode']}. Reader step: {result['reader_note']}", "",
        "## What was compared", "",
        "- **A, paperwork only.** Read the bill, match it to the purchase order (quantity still open on the order, rate, maths), "
        "enter it if it matches. No goods are looked at.",
        "- **B, paperwork plus goods.** Also count every delivery photo with SAM 3.1 (duplicate photos removed, all receiving "
        "events on the order added up), match against what was received, and run the Investigator on every mismatch.",
        "- Both use the same guards: masking, hidden text detection, and payment details taken only from the supplier master.", "",
        "## Result", "",
        "| Measure | A paperwork only | B paperwork plus goods |", "| --- | --- | --- |",
        f"| Deliveries | {a['deliveries']} | {b['deliveries']} |",
        f"| Bad bills in the set (should not be entered as billed) | {a['should_hold']} | {b['should_hold']} |",
        f"| Errors caught (bad bill held) | {a['errors_caught']} | {b['errors_caught']} |",
        f"| Errors missed (bad bill entered) | {a['errors_missed']} | {b['errors_missed']} |",
        f"| Wrong payments avoided (Rs, synthetic) | {a['wrong_payments_avoided_inr']:,.2f} | {b['wrong_payments_avoided_inr']:,.2f} |",
        f"| Wrong payments made (Rs, synthetic) | {a['wrong_payments_made_inr']:,.2f} | {b['wrong_payments_made_inr']:,.2f} |",
        f"| False holds (good bill held) | {a['false_holds']} | {b['false_holds']} |",
        f"| Good bills entered | {a['correctly_entered']} of {a['should_enter']} | {b['correctly_entered']} of {b['should_enter']} |",
        f"| Mean processing time per delivery, this run | {a['mean_seconds_per_case']} s | {b['mean_seconds_per_case']} s |", "",
        f"SAM 3.1 counted {result['sam']['exactly_right']} of {result['sam']['photos']} unique photos exactly right"
        + (f" (wrong: {', '.join(f'{w['photo']} counted {w['counted']}, true {w['true']}' for w in result['sam']['wrong'])})."
           if result["sam"]["wrong"] else "."), "",
        f"Recorded SAM 3.1 inference time behind B: {result['sam_seconds_total']} s over the whole set "
        f"(about {result['sam_seconds_per_delivery']} s per delivery). The processing times above replay those counts from the "
        "cache when the counter is `recorded`, so the recorded inference time is the honest cost of the goods check on this CPU.", "",
        "## By category", "", "| Category | Deliveries | Should enter | A entered | B entered |", "| --- | --- | --- | --- | --- |"]
    for category, entry in result["by_category"].items():
        lines.append(f"| {category.replace('_', ' ')} | {entry['deliveries']} | {'yes' if entry['should_enter'] else 'no'} | "
                     f"{entry['a_entered']} | {entry['b_entered']} |")
    lines += ["", "## Every delivery", "",
              "| Id | Category | Total (Rs) | Should enter | A | B | B counted | B proposal |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for ra, rb in zip(result["rows_a"], result["rows_b"]):
        lines.append(f"| {ra['id']} | {ra['category'].replace('_', ' ')} | {ra['total_inr']:,.2f} | {'yes' if ra['should_enter'] else 'no'} | "
                     f"{'entered' if ra['entered'] else 'held'} | {'entered' if rb['entered'] else 'held'} | {rb['counted']} | {rb['proposal']} |")
    lines += ["", "## Notes", "",
              "- Pipeline B's findings in this run are written by code from the evidence (`template`), because writing 30 findings "
              "with Muse Glimmer at 1 token per second is not practical here. Every citation in them was still checked by code. "
              "Findings written by Muse Glimmer for the demo cases are recorded in `fixtures/recorded/glimmer`.",
              f"- Receipts verified offline: A {a['receipts']} receipts, B {b['receipts']} receipts.",
              "- A bad bill is one that should not be entered as billed: short delivery, rate above the order, a repeat of goods "
              "already billed, or a split delivery that ends short. Hidden text injection bills are otherwise correct and both "
              "pipelines enter them with payment details from the supplier master."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--counter", choices=("live", "recorded"), default="recorded")
    parser.add_argument("--out", default=str(ROOT / "docs"))
    args = parser.parse_args()
    from .app import load_env
    load_env()
    world = json.loads((FIXTURES / "benchmark.json").read_text(encoding="utf-8"))
    counter = SamCounter(os.environ.get("RELAYLOOM_SAM_PYTHON", ""), os.environ.get("RELAYLOOM_SAM_WEIGHTS", ""),
                         "SAM 3.1 (sam3.1_multiplex.pt), Ultralytics, CPU, this laptop", live=args.counter == "live")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        print(f"Benchmark: {len(world['deliveries'])} deliveries, counter {args.counter}", flush=True)
        rows_a, rec_a = run_pipeline("A", False, world, counter, work)
        print("A paperwork only done", flush=True)
        rows_b, rec_b = run_pipeline("B", True, world, counter, work)
        print("B paperwork plus goods done", flush=True)
    sam = sam_accuracy(world, counter)
    sam_total = 0.0
    for event in world["receiving_events"]:
        for photo in event["photos"]:
            path = counter.path(photo["id"], world["items"][event["item_code"]]["prompt"])
            if path.exists():
                sam_total += json.loads(path.read_text(encoding="utf-8"))["result"].get("infer_seconds", 0)
    result = {"date": time.strftime("%Y-%m-%d %H:%M %z"), "machine": f"{platform.processor() or platform.machine()}, CPU only",
              "counter_mode": "SAM 3.1 live, results cached" if args.counter == "live" else "SAM 3.1 recorded counts from earlier real runs",
              "reader_note": "bills come from the generator's structured bill, not from Muse Glimmer (see docs/BENCHMARK.md header).",
              "pipeline_a": {**score(rows_a), **rec_a}, "pipeline_b": {**score(rows_b), **rec_b},
              "rows_a": rows_a, "rows_b": rows_b, "by_category": by_category(rows_a, rows_b), "sam": sam,
              "sam_seconds_total": round(sam_total, 1), "sam_seconds_per_delivery": round(sam_total / len(rows_b), 1)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark-results.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    write_markdown(result, out / "BENCHMARK.md")
    print(json.dumps({"A": result["pipeline_a"] | {"receipts": 0}, "B": result["pipeline_b"] | {"receipts": 0}}, indent=1))
    sys.exit(0 if rec_a["verified"] and rec_b["verified"] else 1)


if __name__ == "__main__":
    main()
