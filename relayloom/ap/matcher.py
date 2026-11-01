"""Three way match in code: purchase order, bill and goods received, as a running total per purchase order.

Goods received are the sum over every receiving event of the order. Earlier bills on the same order count
against what has been received, so partial deliveries and partial bills add up per order, not per bill.
"""
from __future__ import annotations


def match(po: dict, bill: dict, received: dict[str, int] | None, billed_before: dict[str, float], limits: dict) -> dict:
    """Compare every PO line with the bill line, the goods received and what was already billed.

    received maps item_code to the total counted over all receiving events of this order. None means the
    paperwork only check: the goods are not looked at (used by the benchmark baseline).
    """
    qty_tol = limits["quantity_tolerance_units"]
    rate_tol = limits["rate_tolerance_percent"] / 100
    rows, problems = [], []
    if bill["po_number"] != po["po_number"]:
        problems.append(f"bill cites {bill['po_number']}, expected {po['po_number']}")
    if bill["supplier_id"] != po["supplier_id"]:
        problems.append(f"bill supplier {bill['supplier_id']} is not the PO supplier {po['supplier_id']}")
    billed = {line["item_code"]: line for line in bill["lines"]}
    for item in po["items"]:
        code = item["item_code"]
        line = billed.pop(code, None)
        before = billed_before.get(code, 0)
        got = None if received is None else received.get(code, 0)
        row = {"item_code": code, "description": item["description"], "po_qty": item["qty"], "po_rate": item["rate_inr"],
               "bill_qty": line["qty"] if line else None, "bill_rate": line["rate_inr"] if line else None,
               "received": got, "billed_before": before, "issues": []}
        if line is None:
            row["issues"].append("not on bill")
        else:
            if line["qty"] + before > item["qty"] + qty_tol:
                row["issues"].append(f"billed {line['qty']:g} with {before:g} already billed, ordered {item['qty']:g}")
            if abs(line["rate_inr"] - item["rate_inr"]) > item["rate_inr"] * rate_tol:
                row["issues"].append(f"rate {line['rate_inr']:.2f}, PO rate {item['rate_inr']:.2f}")
            if abs(line["qty"] * line["rate_inr"] - line["amount_inr"]) > limits["total_tolerance_inr"]:
                row["issues"].append("line amount is not qty times rate")
            if got is not None and line["qty"] + before > got + qty_tol:
                row["issues"].append(f"billed {line['qty']:g} with {before:g} already billed, received {got:g}")
        rows.append(row)
        problems.extend(f"{code}: {issue}" for issue in row["issues"])
    for code in billed:
        problems.append(f"{code}: billed but not on the PO")
    subtotal = round(sum(line["amount_inr"] for line in bill["lines"]), 2)
    if abs(subtotal + bill["tax_inr"] - bill["total_inr"]) > limits["total_tolerance_inr"]:
        problems.append(f"total {bill['total_inr']:.2f} is not lines {subtotal:.2f} plus tax {bill['tax_inr']:.2f}")
    expected_tax = round(subtotal * po.get("tax_rate", 0), 2)
    if abs(expected_tax - bill["tax_inr"]) > limits["total_tolerance_inr"]:
        problems.append(f"tax {bill['tax_inr']:.2f}, expected {expected_tax:.2f} at the PO tax rate")
    over_limit = bill["total_inr"] > limits["owner_amount_limit_inr"]
    return {"matched": not problems, "rows": rows, "problems": problems, "subtotal_inr": subtotal,
            "over_limit": over_limit, "goods_checked": received is not None}
