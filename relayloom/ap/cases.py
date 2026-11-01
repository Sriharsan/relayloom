"""The five demo cases, one command each, PASS or FAIL per check.

python -m relayloom.ap.cases match|short|price|injection|netcut|all [--live | --reader ... --counter ... --ledger ...]
Default is rehearsal: recorded Glimmer and SAM 3.1 outputs from real runs, built in ledger.
Every run prints which model route and which ledger it used.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from .app import build, load_env
from .receipts import verify

CASES = ("match", "short", "price", "injection", "netcut")


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
    return (f"read {reader.get('seconds')} s via {reader.get('route')}; counted {counter.get('count')} in "
            f"{counter.get('seconds')} s via {counter.get('route')}")


def run_match(bench, c):
    [case] = bench.run_batch(records(bench, "match"))
    print("  " + summary(case))
    c.check("bill read into the strict schema", case.bill is not None)
    c.check("SAM 3.1 counted 24 tins", case.counter.get("count") == 24, case.counter.get("count"))
    c.check("three way match passed", case.match and case.match["matched"])
    c.check("entered with no person involved", case.decision is None and case.invoice_id, case.status)
    c.check("Checker read every field back from the ledger", case.state == "entered_checked", case.status)
    c.check("exactly one invoice in the ledger", bench.ledger.count_invoices(case.supplier_id, case.bill_no) == 1)


def run_short(bench, c, decision="approve"):
    name = "short"
    [case] = bench.run_batch(records(bench, name))
    print("  " + summary(case))
    c.check("delivery counted short", case.counter.get("count", 99) < case.bill["lines"][0]["qty"], case.counter.get("count"))
    c.check("held for the owner, nothing entered", case.state == "held_for_owner" and
            bench.ledger.find_invoice(case.supplier_id, case.bill_no) is None, case.status)
    c.check("dispute drafted by Muse Glimmer", bool(case.dispute and case.dispute["text"]), case.dispute and case.dispute["route"])
    c.check("dispute not sent before approval", case.dispute and not case.dispute["sent"])
    bench.decide(case.id, decision, "Owner")
    c.check("owner decision recorded with policy hash", case.decision and case.decision["policy_hash"] == bench.policy.hash)
    c.check("browser agent filed the dispute in the supplier portal", case.state == "dispute_sent", case.status)
    c.check("bill still not entered", bench.ledger.find_invoice(case.supplier_id, case.bill_no) is None)


def run_price(bench, c):
    [case] = bench.run_batch(records(bench, "price"))
    print("  " + summary(case))
    c.check("rate above the PO rate caught", case.match and any("rate 18.50" in p for p in case.match["problems"]),
            case.match and case.match["problems"])
    c.check("held for the owner", case.state == "held_for_owner", case.status)
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
