"""Run the relayloom command against real purchase orders from the State of California open data, with the exception
types that published accounts payable sources describe. Nothing here is invented: the items, quantities, prices, suppliers
and purchase order numbers are rows of the public dataset, and each exception is a documented real-world case.

Usage:
  python scripts/real_world_check.py --fetch      download rows from data.ca.gov into data/real-world/ca_po_raw.json (needs the network)
  python scripts/real_world_check.py --sample     pick the committed sample, tests/data/ca_po_sample.json
  python scripts/real_world_check.py [--md docs/REAL_WORLD_CHECK.md]    run every case through the command

Source of the rows: State of California, Purchase Order Data 2012-2015, https://data.ca.gov/dataset/purchase-order-data
(resource bb82edc5-9c78-44e2-8947-68ece26197c5). The catalog entry lists no licence, so only a small cited sample is kept here.
"""
import contextlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import time
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom import cli  # noqa: E402

RAW = ROOT / "data" / "real-world" / "ca_po_raw.json"
SAMPLE = ROOT / "tests" / "data" / "ca_po_sample.json"
URL = "https://data.ca.gov/api/3/action/datastore_search?resource_id=bb82edc5-9c78-44e2-8947-68ece26197c5&limit=3000"
SOURCES = {
    "partial shipment": "Paystream and Corpay describe a purchase order for 100 units at $10 where the dock logs 90 and the vendor still bills 100",
    "billed above received": "Sage describes an invoice for 101 laptops where the receiving report confirmed 100",
    "unit of measure": "Peakflo and Centime describe a purchase order for 96 bottles at $7.50 invoiced as 4 cartons; both totals agree, the lines do not",
    "price above the order": "Ardent Partners: price and quantity tolerances are the main lever for match exceptions",
    "wrong order number": "Tradogram lists a PO mismatch as a standard header check",
}


def money(text):
    return float(re.sub(r"[^0-9.\-]", "", text or "") or 0)


def fetch():
    import urllib.request
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(urllib.request.urlopen(URL, timeout=120).read())
    print("saved", RAW)


def pick_sample():
    rows = json.loads(RAW.read_text(encoding="utf-8"))["result"]["records"]
    by_po = {}
    for r in rows:
        by_po.setdefault(r["Purchase Order Number"], []).append(r)
    chosen = []
    singles = [v for v in by_po.values() if len(v) == 1 and v[0]["Quantity"] and v[0]["Unit Price"]]
    singles.sort(key=lambda v: (v[0]["Quantity"], v[0]["Item Name"] or ""))
    step = max(1, len(singles) // 45)
    chosen += singles[::step][:45]
    chosen += [v for v in singles if v[0]["Quantity"] != int(v[0]["Quantity"])][:8]            # fractional quantities (hours, weights)
    chosen += [v for v in singles if re.search(r"[^\x00-\x7f]", v[0]["Item Name"] or "")][:2]    # broken characters in real names
    chosen += sorted(singles, key=lambda v: -v[0]["Quantity"])[:4]                              # the largest quantities
    multi = sorted((v for v in by_po.values() if len(v) > 1), key=lambda v: len(v))
    chosen += multi[::max(1, len(multi) // 18)][:18] + multi[-3:]                               # multi line orders up to 12 lines
    chosen += [v for v in by_po.values() if any(not r["Quantity"] or not r["Unit Price"] for r in v)][:5]  # rows with missing values
    seen, out = set(), []
    for group in chosen:
        key = group[0]["Purchase Order Number"]
        if key not in seen:
            seen.add(key)
            out.append([{k: r[k] for k in ("Purchase Order Number", "Supplier Code", "Supplier Name", "Item Name", "Item Description", "Quantity",
                                           "Unit Price", "Total Price", "Acquisition Type", "Fiscal Year", "Department Name")} for r in group])
    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE.write_text(json.dumps({"source": "State of California, Purchase Order Data 2012-2015, https://data.ca.gov/dataset/purchase-order-data",
                                  "note": "Public data. The catalog entry lists no licence, so only this small cited sample is kept.", "orders": out}, indent=1, ensure_ascii=True), encoding="utf-8")
    print(len(out), "purchase orders saved to", SAMPLE)


def build(group):
    """A purchase order and the matching bill from real rows. Returns (po, bill, quantities, problems_with_the_row)."""
    first = group[0]
    items, lines, quantities = [], [], {}
    for n, r in enumerate(group, start=1):
        qty, rate = r["Quantity"], money(r["Unit Price"])
        code = f"L{n}"
        name = (r["Item Name"] or r["Item Description"] or "item").strip()[:80]
        items.append({"item_code": code, "description": name, "qty": qty, "rate_inr": rate})
        if qty and rate is not None:
            lines.append({"item_code": code, "description": name, "qty": qty, "rate_inr": rate, "amount_inr": round(qty * rate, 2)})
        quantities[code] = qty
    total = round(sum(line["amount_inr"] for line in lines), 2)
    supplier = f"SUP-{first['Supplier Code']}"
    po = {"po_number": first["Purchase Order Number"], "supplier_id": supplier, "tax_rate": 0, "items": items}
    bill = {"supplier_id": supplier, "bill_no": f"INV-{first['Purchase Order Number']}", "bill_date": "2014-01-15", "po_number": first["Purchase Order Number"],
            "lines": lines, "tax_inr": 0.0, "total_inr": total}
    return po, bill, quantities


def variants(po, bill, quantities):
    """(kind, bill, counted, expected exit code, phrase) for one real purchase order, one case per documented exception."""
    import copy
    from relayloom.ap.policy import load_policy
    limit = load_policy().limits["owner_amount_limit_inr"]
    # an exact delivery is clear, unless the bill is above the owner's approval limit, which holds it for a person
    out = [("exact delivery" if bill["total_inr"] <= limit else "exact delivery, above the approval limit", bill, dict(quantities),
            0 if bill["total_inr"] <= limit else 3, "CLEAR TO ENTER" if bill["total_inr"] <= limit else "approval limit")]
    first = po["items"][0]
    q = quantities["L1"]
    if q >= 2:
        short = dict(quantities)
        short["L1"] = int(q * 0.9) if q * 0.9 < q and int(q * 0.9) != q else q - 1
        out.append(("partial shipment", bill, short, 3, "HELD"))
    over = copy.deepcopy(bill)
    over["lines"][0]["qty"] = q + 1
    over["lines"][0]["amount_inr"] = round((q + 1) * over["lines"][0]["rate_inr"], 2)
    over["total_inr"] = round(sum(line["amount_inr"] for line in over["lines"]), 2)
    out.append(("billed above received", over, dict(quantities), 3, "HELD"))
    if first["rate_inr"] >= 1:
        pricey = copy.deepcopy(bill)
        pricey["lines"][0]["rate_inr"] = round(first["rate_inr"] * 1.05, 2)
        pricey["lines"][0]["amount_inr"] = round(q * pricey["lines"][0]["rate_inr"], 2)
        pricey["total_inr"] = round(sum(line["amount_inr"] for line in pricey["lines"]), 2)
        out.append(("price above the order", pricey, dict(quantities), 3, "rate "))
    if q >= 6 and q == int(q) and q % 6 == 0:
        packs = copy.deepcopy(bill)
        packs["lines"][0]["qty"] = q / 6
        packs["lines"][0]["rate_inr"] = round(first["rate_inr"] * 6, 2)
        packs["lines"][0]["amount_inr"] = round((q / 6) * packs["lines"][0]["rate_inr"], 2)
        packs["total_inr"] = round(sum(line["amount_inr"] for line in packs["lines"]), 2)
        out.append(("unit of measure", packs, dict(quantities), 3, "unit of measure"))
    wrong = copy.deepcopy(bill)
    wrong["po_number"] = "PO-WRONG-1"
    out.append(("wrong order number", wrong, dict(quantities), 3, "expected"))
    return out


def run_case(po, bill, counted):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "po.json").write_text(json.dumps(po), encoding="utf-8")
        (base / "bill.json").write_text(json.dumps(bill), encoding="utf-8")
        argv = ["check", "--bill-json", str(base / "bill.json"), "--po", str(base / "po.json"), "--out", str(base / "out")]
        (base / "counts.json").write_text(json.dumps(counted), encoding="utf-8")
        argv += ["--counts-file", str(base / "counts.json")]
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "HOME", base / "home"), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(argv)
            verified = io.StringIO()
            with contextlib.redirect_stdout(verified):
                chain_ok = cli.main(["verify", str(base / "out" / "receipts.jsonl")]) == 0 if code in (0, 3) else True
        return code, out.getvalue() + err.getvalue(), chain_ok


def main():
    args = sys.argv[1:]
    if "--fetch" in args:
        return fetch()
    if "--sample" in args:
        return pick_sample()
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))["orders"]
    rows, started = [], time.time()
    for group in data:
        po, bill, quantities = build(group)
        label = f"{po['po_number']} ({len(po['items'])} line{'s' if len(po['items']) > 1 else ''}, {group[0]['Item Name'][:34] if group[0]['Item Name'] else 'no name'})"
        if not bill["lines"] or len(bill["lines"]) != len(po["items"]) or any(not i["qty"] or i["rate_inr"] is None for i in po["items"]):
            code, text, chain_ok = run_case(po, bill if bill["lines"] else {**bill, "lines": []}, {k: (v or 0) for k, v in quantities.items()})
            ok = code == 2 and "relayloom:" in text and "Traceback" not in text
            rows.append((label, "row with a missing quantity or price", 2, code, ok, text.strip().splitlines()[-1][:90] if text.strip() else ""))
            continue
        for kind, b, counted, expected, phrase in variants(po, bill, quantities):
            code, text, chain_ok = run_case(po, b, counted)
            ok = code == expected and phrase.lower() in text.lower() and "Traceback" not in text and chain_ok
            rows.append((label, kind, expected, code, ok, "" if ok else text.strip().splitlines()[-1][:120]))
    passed = sum(1 for r in rows if r[4])
    print(f"{passed} of {len(rows)} cases passed in {round(time.time() - started, 1)} s")
    for r in rows:
        if not r[4]:
            print("FAIL", r[0], "|", r[1], "| wanted", r[2], "got", r[3], "|", r[5])
    if "--md" in args:
        kinds = {}
        for r in rows:
            kinds.setdefault(r[1], [0, 0])[0] += 1
            kinds[r[1]][1] += r[4]
        lines = ["# Real world check", "", f"Run {time.strftime('%Y-%m-%d %H:%M %z')} by `python scripts/real_world_check.py`. {len(data)} real purchase orders from the State of California",
                 "open data (items, quantities, prices, suppliers and order numbers are rows of the public dataset), each run through `relayloom check` and `relayloom verify`",
                 "with the exception types published accounts payable sources describe.", "",
                 "Dataset: [State of California, Purchase Order Data 2012-2015](https://data.ca.gov/dataset/purchase-order-data). The catalog lists no licence, so only a small cited sample is kept in the repository.", "",
                 "| Exception type | Cases | Passed | Where the type comes from |", "| --- | --- | --- | --- |"]
        for kind, (n, ok) in sorted(kinds.items()):
            lines.append(f"| {kind} | {n} | {ok} | {SOURCES.get(kind, 'real rows with data the order system left empty')} |")
        lines += ["", f"{passed} of {len(rows)} cases passed.", "", "What the real data taught the command: fractional quantities (hours and weights) need decimal counts, "
                  "purchase orders go up to 12 lines so counts come from a file, some rows have no quantity or price, some names carry broken characters, "
                  "and unit of measure differences need their own hint because both totals agree.", ""]
        failed = [r for r in rows if not r[4]]
        if failed:
            lines += ["## Cases that failed", ""] + [f"- {r[0]} | {r[1]}: wanted exit {r[2]}, got {r[3]}. {r[5]}" for r in failed]
        Path(args[args.index("--md") + 1]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
