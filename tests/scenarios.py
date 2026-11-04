"""Forty scenarios for the relayloom command line, in groups: typical, varied, extreme, repeated, and damaged receipts.

Shared by tests/test_scenarios.py (every scenario must behave as listed) and scripts/package_scenarios.py (which writes the
table in docs/PACKAGE_SCENARIOS.md). Each scenario runs the real command, in a fresh folder, and says what it expects:
the exit code (0 clear, 3 held, 2 could not run, 1 broken chain) and a phrase that must appear.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import mock

from relayloom import cli

LINE = {"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0, "amount_inr": 5900.0}
LINE2 = {"item_code": "CAN-5L", "description": "Coolant can 5 litre", "qty": 20, "rate_inr": 410.0, "amount_inr": 8200.0}
BILL = {"supplier_id": "SUP-CALDER", "bill_no": "CAL-0990", "bill_date": "2026-11-01", "po_number": "PO-1", "lines": [LINE],
        "tax_inr": 1062.0, "total_inr": 6962.0}
PO = {"po_number": "PO-1", "supplier_id": "SUP-CALDER", "tax_rate": 0.18,
      "items": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0}]}


def bill(**changes):
    b = copy.deepcopy(BILL)
    b.update(changes)
    return b


def two_line_bill(second_qty=20):
    line2 = {**LINE2, "qty": second_qty, "amount_inr": second_qty * 410.0}
    sub = 5900.0 + line2["amount_inr"]
    return bill(lines=[LINE, line2], tax_inr=round(sub * 0.18, 2), total_inr=round(sub * 1.18, 2))


def two_line_po():
    po = copy.deepcopy(PO)
    po["items"].append({"item_code": "CAN-5L", "description": "Coolant can 5 litre", "qty": 20, "rate_inr": 410.0})
    return po


def one(counted, **kw):
    return {"bill": BILL, "po": PO, "args": ["--counted", str(counted)], **kw}


# group, name, spec, expected exit code, phrase that must appear in the output
SCENARIOS = [
    # typical deliveries
    ("typical", "exact delivery", one(50), 0, "CLEAR TO ENTER"),
    ("typical", "short by one", one(49), 3, "received 49"),
    ("typical", "short by four", one(46), 3, "received 46"),
    ("typical", "short by ten percent", one(45), 3, "received 45"),
    ("typical", "delivered more than billed", one(55), 0, "CLEAR TO ENTER"),
    ("typical", "price above the order", {"bill": bill(lines=[{**LINE, "rate_inr": 125.0, "amount_inr": 6250.0}], tax_inr=1125.0, total_inr=7375.0), "po": PO,
                                           "args": ["--counted", "50"]}, 3, "rate 125.00"),
    ("typical", "tax is wrong", {"bill": bill(tax_inr=900.0, total_inr=6800.0), "po": PO, "args": ["--counted", "50"]}, 3, "tax 900.00"),
    ("typical", "total is not lines plus tax", {"bill": bill(total_inr=7500.0), "po": PO, "args": ["--counted", "50"]}, 3, "is not lines"),
    ("typical", "bill cites another order", {"bill": bill(po_number="PO-9"), "po": PO, "args": ["--counted", "50"]}, 3, "expected PO-1"),
    ("typical", "bill from the wrong supplier", {"bill": bill(supplier_id="SUP-OTHER"), "po": PO, "args": ["--counted", "50"]}, 3, "not the PO supplier"),
    # varied inputs
    ("varied", "two lines, both delivered", {"bill": two_line_bill(), "po": two_line_po(), "args": ["--counted", "CARTON-HD=50", "CAN-5L=20"]}, 0, "CLEAR TO ENTER"),
    ("varied", "two lines, the second is short", {"bill": two_line_bill(), "po": two_line_po(), "args": ["--counted", "CARTON-HD=50", "CAN-5L=17"]}, 3, "CAN-5L"),
    ("varied", "two lines, one count missing", {"bill": two_line_bill(), "po": two_line_po(), "args": ["--counted", "CARTON-HD=50"]}, 2, "Missing: CAN-5L"),
    ("varied", "bill lines in a different order", {"bill": (lambda b: b.update(lines=b["lines"][::-1]) or b)(two_line_bill()), "po": two_line_po(),
                                                   "args": ["--counted", "CARTON-HD=50", "CAN-5L=20"]}, 0, "CLEAR TO ENTER"),
    ("varied", "a line billed that is not on the order", {"bill": two_line_bill(), "po": PO, "args": ["--counted", "CARTON-HD=50"]}, 3, "not on the PO"),
    ("varied", "photos count the second line, the first is given", {"bill": two_line_bill(), "po": two_line_po(),
                                                                 "args": ["--item", "CAN-5L", "--counted", "CARTON-HD=50", "CAN-5L=20"]}, 0, "CLEAR TO ENTER"),
    ("varied", "a count for a line that is not on the order", {"bill": BILL, "po": PO, "args": ["--counted", "NOPE=3"]}, 2, "is not on the purchase order"),
    ("varied", "kilograms with a fraction, counted short", {"bill": bill(lines=[{**LINE, "qty": 12.5, "amount_inr": 1475.0}], tax_inr=265.5, total_inr=1740.5),
                                                          "po": {**PO, "items": [{**PO["items"][0], "qty": 12.5}]}, "args": ["--counted", "12"]}, 3, "received 12"),
    ("varied", "a folder path with spaces and accents", {**one(50), "folder": "Rechnung März 2026 (copy)"}, 0, "CLEAR TO ENTER"),
    ("varied", "a bill number with slashes and spaces", {"bill": bill(bill_no="INV/2026-11/0001 A"), "po": PO, "args": ["--counted", "50"]}, 0, "INV/2026-11/0001 A"),
    ("varied", "json output for a script", {"bill": BILL, "po": PO, "args": ["--counted", "46", "--json"]}, 3, '"state": "held"'),
    # extreme inputs
    ("extreme", "nothing arrived", one(0), 3, "received 0"),
    ("extreme", "a million items counted", one(1000000), 0, "CLEAR TO ENTER"),
    ("extreme", "a negative count", one(-3), 2, "negative"),
    ("extreme", "a count that is not a number", {"bill": BILL, "po": PO, "args": ["--counted", "many"]}, 2, "must be a number"),
    ("extreme", "a count with decimals is valid (weights, hours)", {"bill": BILL, "po": PO, "args": ["--counted", "49.5"]}, 3, "received 49.5"),
    ("extreme", "a bill over the owner approval limit", {"bill": bill(lines=[{**LINE, "qty": 1000, "amount_inr": 118000.0}], tax_inr=21240.0, total_inr=139240.0),
                                                        "po": {**PO, "items": [{**PO["items"][0], "qty": 1000}]}, "args": ["--counted", "1000"]}, 3, "approval limit"),
    ("extreme", "a bill number of 500 characters", {"bill": bill(bill_no="B" * 500), "po": PO, "args": ["--counted", "50"]}, 2, "short code"),
    ("extreme", "a bill number that carries symbols for an instruction", {"bill": bill(bill_no="A&B;rm -rf"), "po": PO, "args": ["--counted", "50"]}, 2, "short code"),
    ("extreme", "bank details smuggled into the bill", {"bill": {**BILL, "bank_account": "123456789012"}, "po": PO, "args": ["--counted", "50"]}, 2, "bill schema"),
    ("extreme", "an empty bill file", {"raw_bill": "", "po": PO, "args": ["--counted", "50"]}, 2, "not valid JSON"),
    ("extreme", "a purchase order that is a list", {"bill": BILL, "raw_po": "[1, 2, 3]", "args": ["--counted", "50"]}, 2, "relayloom:"),
    ("extreme", "a purchase order with no lines", {"bill": BILL, "po": {**PO, "items": []}, "args": ["--counted", "50"]}, 2, "items list"),
    ("extreme", "a bill with a quantity of zero", {"bill": bill(lines=[{**LINE, "qty": 0, "amount_inr": 0.0}], tax_inr=0.0, total_inr=0.0), "po": PO, "args": ["--counted", "0"]}, None, "relayloom|Bill"),
    ("extreme", "no count and no photos", {"bill": BILL, "po": PO, "args": []}, 2, "give --photos"),
    # repeated and shared use
    ("repeated", "the same check five times in one folder", {"bill": BILL, "po": PO, "args": ["--counted", "46"], "repeat": 5}, 3, "chain verified"),
    ("repeated", "two different bills in one folder", {"bill": BILL, "po": PO, "args": ["--counted", "46"], "second_case": True}, 3, "chain verified"),
    ("repeated", "four processes writing the same folder at once", {"bill": BILL, "po": PO, "args": ["--counted", "46"], "parallel": 4}, 3, "chain verified"),
    # damaged receipts
    ("receipts", "a receipt file with a line cut off", {**one(46), "damage": "truncate"}, 2, "not a receipt file"),
    ("receipts", "an empty receipt file", {**one(46), "damage": "empty"}, 1, "nothing to verify"),
    ("receipts", "a middle receipt deleted", {**one(46), "damage": "delete"}, 1, "BROKEN"),
    ("receipts", "a receipt copied twice", {**one(46), "damage": "duplicate"}, 1, "BROKEN"),
    ("receipts", "receipts in a different order", {**one(46), "damage": "reorder"}, 1, "BROKEN"),
    ("receipts", "someone else's public key", {**one(46), "damage": "wrongkey"}, 1, "BROKEN"),
]


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(argv)
        except SystemExit as stop:
            code = stop.code if isinstance(stop.code, int) else 2
            err.write(str(stop.code) if isinstance(stop.code, str) else "")
    return code, out.getvalue() + err.getvalue()


def damage_receipts(path: Path, kind: str, keyfile: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if kind == "truncate":
        path.write_text("\n".join(lines[:-1] + [lines[-1][: len(lines[-1]) // 2]]), encoding="utf-8")
    elif kind == "empty":
        path.write_text("", encoding="utf-8")
    elif kind == "delete":
        del lines[1]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif kind == "duplicate":
        path.write_text("\n".join(lines[:2] + [lines[1]] + lines[2:]) + "\n", encoding="utf-8")
    elif kind == "reorder":
        lines[0], lines[1] = lines[1], lines[0]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif kind == "wrongkey":
        from relayloom.ap.receipts import Signer
        other = Signer(path.parent / "other.key")
        keyfile.write_text(other.public_key, encoding="utf-8")


def run_scenario(group, name, spec, expected_code, phrase):
    """Run one scenario in a fresh folder. Returns (code, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / spec.get("folder", "work")
        base.mkdir(parents=True)
        (base / "bill.json").write_text(spec["raw_bill"] if "raw_bill" in spec else json.dumps(spec["bill"], ensure_ascii=False), encoding="utf-8")
        (base / "po.json").write_text(spec["raw_po"] if "raw_po" in spec else json.dumps(spec["po"], ensure_ascii=False), encoding="utf-8")
        out = base / "out"
        argv = ["check", "--bill-json", str(base / "bill.json"), "--po", str(base / "po.json"), "--out", str(out)] + spec["args"]
        with mock.patch.object(cli, "HOME", Path(tmp) / "home"):
            if spec.get("parallel"):
                env = {**__import__("os").environ, "RELAYLOOM_HOME": str(Path(tmp) / "home"), "PYTHONUTF8": "1"}
                procs = [subprocess.Popen([sys.executable, "-m", "relayloom.cli"] + argv[:-0 or None], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                         for _ in range(spec["parallel"])]
                codes = [p.wait(120) for p in procs]
                verified, text = run_cli(["verify", str(out / "receipts.jsonl")])
                return (3 if verified == 0 and all(c == 3 for c in codes) else 99), text
            code, text = run_cli(argv)
            for _ in range(spec.get("repeat", 1) - 1):
                code, text = run_cli(argv)
            if spec.get("second_case"):
                run_cli(argv + ["--case", "second-bill"])
            if spec.get("repeat") or spec.get("second_case"):
                verified, text = run_cli(["verify", str(out / "receipts.jsonl")])
                return (code if verified == 0 else 99), text
            if spec.get("damage"):
                damage_receipts(out / "receipts.jsonl", spec["damage"], out / "public_key.txt")
                return run_cli(["verify", str(out / "receipts.jsonl")])
            return code, text
