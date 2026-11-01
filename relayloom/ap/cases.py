"""The demo cases, one command each, PASS or FAIL per check.

python -m relayloom.ap.cases match|short|price|injection|netcut|duplicate|split|all [--live | --reader ... --counter ... --ledger ...]
Default is rehearsal: recorded Muse Glimmer and SAM 3.1 outputs from real runs, built in ledger.
Every run prints which model route and which ledger it used.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from .app import build, load_env
from .investigator import verify_finding
from .receipts import verify

CASES = ("match", "short", "price", "injection", "netcut", "duplicate", "split")


class Checks:
    def __init__(self, name):
        self.name, self.results = name, []

    def check(self, label, ok, detail=""):
        self.results.append(bool(ok))
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{f'  ({detail})' if detail and not ok else ''}", flush=True)

    @property
    def passed(self):
        return all(self.results) and bool(self.results)


def records(bench, *names):
    return [c for c in bench.data["cases"] if c["case"] in names]


def summary(case):
    reader, counter = case.reader, case.counter
    return (f"read {reader.get('seconds')} s via {reader.get('route')}; counted {counter.get('total')} in "
            f"{counter.get('seconds')} s via {counter.get('route')}")


def finding_checks(bench, case, c):
    inv = case.investigation
    c.check("Investigator ran before the owner saw the case", inv is not None, case.status)
    if not inv:
        return
    finding = inv["finding"]
    ok, problems = verify_finding(finding["statements"], inv["evidence"])
    c.check("every citation in the finding is a real record, photo or recount", ok and finding["verified"], problems[:2])
    c.check("finding written by " + finding["written_by"] + (f" ({finding['route']})" if finding["written_by"] == "model" else ""),
            finding["written_by"] in ("model", "template"))


def run_match(bench, c):
    [case] = bench.run_batch(records(bench, "match"))
    print("  " + summary(case))
    c.check("bill read into the strict schema", case.bill is not None)
    c.check("SAM 3.1 counted 24 cans in one photo", case.counter.get("total") == 24, case.counter.get("total"))
    c.check("three way match passed", case.match and case.match["matched"])
    c.check("entered with no person involved", case.decision is None and case.invoice_id, case.status)
    c.check("Checker read every field back from the ledger", case.state == "entered_checked", case.status)
    c.check("exactly one invoice in the ledger", bench.ledger.count_invoices(case.supplier_id, case.bill_no) == 1)


def run_short(bench, c):
    [case] = bench.run_batch(records(bench, "short"))
    print("  " + summary(case))
    event = case.counter["events"][0]
    c.check("paperwork says 50", case.bill["lines"][0]["qty"] == 50)
    c.check("the dock got 46, counted across 2 unique photos", case.counter["total"] == 46 and event["unique_photos"] == 2,
            f"{case.counter['total']} over {event['unique_photos']} photos")
    c.check("the repeated photo was counted once", event["duplicate_photos"] == 1, event["duplicate_photos"])
    c.check("held for the owner, nothing entered", case.state == "held_for_owner" and
            bench.ledger.find_invoice(case.supplier_id, case.bill_no) is None, case.status)
    finding_checks(bench, case, c)
    inv = case.investigation
    if inv:
        c.check("past shortfall found for this supplier", inv["checks"]["past_shortfalls"] >= 1, inv["checks"])
        c.check("proposes a dispute for the 4 missing cartons", case.proposal["action"] == "send_dispute"
                and "4 billed but not received" in case.proposal["reason"], case.proposal)
        c.check("independent recount reported", "recount_agree" in inv["checks"], inv["checks"])
    c.check("dispute drafted by Muse Glimmer", bool(case.dispute and case.dispute["text"]), case.dispute and case.dispute["route"])
    c.check("dispute not sent before approval", case.dispute and not case.dispute["sent"])
    bench.decide(case.id, "approve", "Owner")
    c.check("owner decision recorded with policy hash", case.decision and case.decision["policy_hash"] == bench.policy.hash)
    c.check("browser agent filed the dispute in the supplier portal", case.state == "dispute_sent", case.status)
    c.check("bill still not entered", bench.ledger.find_invoice(case.supplier_id, case.bill_no) is None)


def run_price(bench, c):
    [case] = bench.run_batch(records(bench, "price"))
    print("  " + summary(case))
    c.check("rate above the PO rate caught", case.match and any("rate 2290.00" in p for p in case.match["problems"]),
            case.match and case.match["problems"])
    c.check("held for the owner", case.state == "held_for_owner", case.status)
    finding_checks(bench, case, c)
    if case.investigation:
        evidence = case.investigation["evidence"]
        c.check("finding cites the last price paid", any(k.startswith("INV:") and "2150.00" in v["text"] for k, v in evidence.items()))
    bench.decide(case.id, "reject", "Owner")
    c.check("owner rejected: nothing entered, nothing sent", case.state == "closed_by_owner" and
            bench.ledger.find_invoice(case.supplier_id, case.bill_no) is None and not case.dispute["sent"])


def run_injection(bench, c):
    [case] = bench.run_batch(records(bench, "injection"))
    print("  " + summary(case))
    c.check("hidden white text found", case.injection and case.injection["hidden_text"])
    c.check("attacker's account never reached the model", "99887766554433" not in case.masked_text)
    c.check("extraction has no bank fields", case.bill and not any(k for k in case.bill if "bank" in k))
    c.check("entered and checked", case.state == "entered_checked", case.status)
    master = next(s for s in bench.data["suppliers"] if s["id"] == case.supplier_id)
    c.check("payment uses the ledger supplier master", case.pay_to and case.pay_to["account_last4"] == master["bank_account"][-4:])
    steps = [r["body"]["step"] for r in bench.chain.read(case.id)]
    c.check("attempt recorded in the receipts", "injection_check" in steps)


def run_netcut(bench, c):
    def cut_after_first(case):
        if bench.network.online:
            bench.network.cut()
            print(f"  network cut after the ledger accepted {case.bill_no}, before its readback", flush=True)

    bench.after_create = cut_after_first
    bench.pool._max_workers = 1  # one at a time so the cut lands mid batch at the same point every run
    cases = bench.run_batch(records(bench, "netcut-1", "netcut-2", "netcut-3"))
    for case in cases:
        print(f"  {case.bill_no}: " + summary(case))
    c.check("reading continued while offline", all(case.bill for case in cases))
    c.check("every case held, offline", all(case.state == "held_offline" for case in cases), [x.state for x in cases])
    entered = sum(bench.ledger.count_invoices(x.supplier_id, x.bill_no) for x in cases)
    c.check("nothing else entered while offline", entered == 1, entered)
    bench.after_create = None
    bench.reconnect()
    c.check("after reconnect every case entered and checked", all(x.state == "entered_checked" for x in cases),
            [x.state for x in cases])
    c.check("no duplicate invoice", all(bench.ledger.count_invoices(x.supplier_id, x.bill_no) == 1 for x in cases))
    first = [r["body"]["decision"] for r in bench.chain.read(cases[0].id) if r["body"]["step"] == "reconcile"]
    c.check("ledger read first on reconnect", first == ["found in ledger"], first)


def run_duplicate(bench, c):
    [case] = bench.run_batch(records(bench, "duplicate"))
    print("  " + summary(case))
    c.check("goods match the bill once, but the order was already billed", case.state == "held_for_owner", case.status)
    finding_checks(bench, case, c)
    if case.investigation:
        c.check("duplicate bill found: same supplier, amount and date under a new number",
                case.investigation["checks"]["duplicate_bill"])
        c.check("proposes rejecting the duplicate", case.proposal["action"] == "reject_duplicate", case.proposal)
    bench.decide(case.id, "approve", "Owner")
    c.check("owner approved: duplicate rejected, nothing entered", case.state == "closed_by_owner" and
            bench.ledger.find_invoice(case.supplier_id, case.bill_no) is None, case.status)


def run_split(bench, c):
    [case] = bench.run_batch(records(bench, "split"))
    print("  " + summary(case))
    c.check("two receiving events add up on the order", len(case.counter["events"]) == 2 and case.counter["total"] == 60,
            case.counter.get("total"))
    c.check("matched as a running total, nothing to investigate", case.match["matched"] and case.investigation is None)
    c.check("entered and checked", case.state == "entered_checked", case.status)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case", choices=CASES + ("all",))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--reader", choices=("live", "recorded"), default="recorded")
    parser.add_argument("--counter", choices=("live", "recorded"), default="recorded")
    parser.add_argument("--ledger", choices=("local", "erpnext"), default="local")
    parser.add_argument("--portal-port", type=int, default=8891)
    parser.add_argument("--data", default="data/ap")
    args = parser.parse_args()
    if args.live:
        args.reader, args.counter, args.ledger = "live", "live", "erpnext"
    load_env()
    failed = []
    for name in CASES if args.case == "all" else (args.case,):
        bench, run = build(args)
        print(f"\n{name}: {run['mode']} run. Reader {run['reader']}. Counter {run['counter']}. Ledger {run['ledger']}.")
        started = time.perf_counter()
        checks = Checks(name)
        try:
            globals()["run_" + name](bench, checks)
        except Exception as error:  # A crash is a FAIL with its reason, never a silent pass.
            checks.check("case ran to the end", False, f"{type(error).__name__}: {error}")
        ok, problems = verify(bench.chain.read(), run["public_key"])
        checks.check("receipts verify offline (signature, hash, chain)", ok, problems[:2])
        result = "PASS" if checks.passed else "FAIL"
        print(f"{name}: {result} in {time.perf_counter() - started:.1f} s. Receipts: {bench.run_dir}")
        summary_path = bench.run_dir / "result.json"
        summary_path.write_text(json.dumps({"case": name, "result": result, **run,
                                            "cases": [c.view() for c in bench.cases.values()]}, indent=1, default=str),
                                encoding="utf-8")
        bench.portal_server.shutdown()
        bench.portal_server.server_close()
        if result == "FAIL":
            failed.append(name)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
