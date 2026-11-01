"""Autonomy policy for accounts payable, read once from a file the model cannot reach."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parent / "policy.json"
LEVELS = ("run_alone", "run_with_approval", "never")
REQUIRED = {
    "read_bill": "run_alone", "count_goods": "run_alone", "match": "run_alone",
    "investigate_mismatch": "run_alone", "hold_bill": "run_alone", "enter_bill_for_received_quantity": "run_with_approval",
    "enter_matching_bill": "run_alone", "check_readback": "run_alone",
    "reconcile_after_reconnect": "run_alone",
    "enter_mismatched_bill": "run_with_approval", "enter_bill_over_limit": "run_with_approval",
    "send_dispute": "run_with_approval", "new_supplier_or_bank_change": "run_with_approval",
    "change_bank_from_invoice_text": "never", "enter_bill_with_failed_readback": "never",
    "change_books_while_offline": "never",
}
LIMIT_BOUNDS = {
    "owner_amount_limit_inr": (1, 10_000_000), "quantity_tolerance_units": (0, 5),
    "rate_tolerance_percent": (0, 5), "total_tolerance_inr": (0, 100),
    "max_count_per_photo": (1, 60), "parallel_cases": (1, 16), "automatic_retries": (0, 0),
}


class Refused(Exception):
    """An action the policy does not allow at this moment."""


class Policy:
    def __init__(self, data: dict, raw: bytes):
        self.data = data
        self.hash = hashlib.sha256(raw).hexdigest()
        self.limits = dict(data["limits"])
        self.allowed_hosts = tuple(sorted(data["egress"]["allowed_hosts"]))

    def level(self, operation: str) -> str:
        return self.data["operations"][operation]["level"]

    def require(self, operation: str, *, approved: bool = False):
        level = self.level(operation)
        if level == "never":
            raise Refused(f"{operation} is never allowed")
        if level == "run_with_approval" and not approved:
            raise Refused(f"{operation} needs the owner's approval")
        return level


def load_policy(path: Path = POLICY_PATH) -> Policy:
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    operations = data.get("operations", {})
    for name, level in REQUIRED.items():
        if operations.get(name, {}).get("level") != level:
            raise ValueError(f"policy must declare {name} at level {level}")
    for name in operations:
        if name not in REQUIRED:
            raise ValueError(f"unknown operation {name}")
    for name, (low, high) in LIMIT_BOUNDS.items():
        value = data.get("limits", {}).get(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not low <= value <= high:
            raise ValueError(f"limit {name} must be between {low} and {high}")
    if data.get("egress", {}).get("default") != "deny":
        raise ValueError("egress default must be deny")
    return Policy(data, raw)
