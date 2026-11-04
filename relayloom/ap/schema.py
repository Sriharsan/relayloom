"""Strict schema for what the Reader may return. Code validates; the model only proposes."""
from __future__ import annotations

import re

BILL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["supplier_id", "bill_no", "bill_date", "po_number", "lines", "tax_inr", "total_inr"],
    "properties": {
        "supplier_id": {"type": "string"},
        "bill_no": {"type": "string"},
        "bill_date": {"type": "string"},
        "po_number": {"type": "string"},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["item_code", "description", "qty", "rate_inr", "amount_inr"],
                "properties": {
                    "item_code": {"type": "string"},
                    "description": {"type": "string"},
                    "qty": {"type": "number"},
                    "rate_inr": {"type": "number"},
                    "amount_inr": {"type": "number"},
                },
            },
        },
        "tax_inr": {"type": "number"},
        "total_inr": {"type": "number"},
    },
}

TOP = set(BILL_SCHEMA["properties"])
LINE = set(BILL_SCHEMA["properties"]["lines"]["items"]["properties"])
FORBIDDEN = re.compile(r"bank|account|ifsc|iban|swift|upi", re.I)
CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9/_.# -]{0,39}$")  # real invoice numbers have slashes and spaces; nothing that can carry an instruction
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Invalid(ValueError):
    pass


def _number(value, name, low=0, high=1_000_000_000):  # real purchase orders reach hundreds of thousands of units and millions in value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        raise Invalid(f"{name} must be a number from {low} to {high}")
    return round(float(value), 2)


def validate_bill(data) -> dict:
    """Return a clean copy or raise Invalid. Unknown keys, bank fields and odd values are refused."""
    if not isinstance(data, dict):
        raise Invalid("bill must be an object")
    keys = set(data)
    if keys - TOP or TOP - keys:
        raise Invalid(f"bill keys must be exactly {sorted(TOP)}")
    for key in ("supplier_id", "bill_no", "po_number"):
        if not isinstance(data[key], str) or not CODE.match(data[key]):
            raise Invalid(f"{key} must be a short code")
    if not isinstance(data["bill_date"], str) or not DATE.match(data["bill_date"]):
        raise Invalid("bill_date must be YYYY-MM-DD")
    lines = data["lines"]
    if not isinstance(lines, list) or not 1 <= len(lines) <= 20:
        raise Invalid("lines must hold 1 to 20 items")
    clean_lines = []
    for index, line in enumerate(lines):
        if not isinstance(line, dict) or set(line) != LINE:
            raise Invalid(f"line {index} keys must be exactly {sorted(LINE)}")
        if not isinstance(line["item_code"], str) or not CODE.match(line["item_code"]):
            raise Invalid(f"line {index} item_code must be a short code")
        if not isinstance(line["description"], str) or len(line["description"]) > 120:
            raise Invalid(f"line {index} description must be text up to 120 characters")
        if FORBIDDEN.search(line["description"]):
            raise Invalid(f"line {index} description mentions payment details")
        clean_lines.append({"item_code": line["item_code"], "description": line["description"],
                            "qty": _number(line["qty"], "qty", 0, 10_000_000),
                            "rate_inr": _number(line["rate_inr"], "rate_inr"),
                            "amount_inr": _number(line["amount_inr"], "amount_inr")})
    return {"supplier_id": data["supplier_id"], "bill_no": data["bill_no"], "bill_date": data["bill_date"],
            "po_number": data["po_number"], "lines": clean_lines,
            "tax_inr": _number(data["tax_inr"], "tax_inr"), "total_inr": _number(data["total_inr"], "total_inr")}
