"""The case file and the supplier file.

When a case ends, the Archivist writes one JSON file with what happened and why: the bill, the count, the likely
cause and the reasons, the owner's decision, the evidence ids, and the supplier's record at that time. Its hash goes
into the signed receipt chain, so the file cannot be changed later without the chain showing it. Later cases read the
supplier file, so a supplier's history informs the next investigation, like notes kept for the next patient.
"""
from __future__ import annotations

import json
from pathlib import Path
import time

from .receipts import sha256


def supplier_file(workbench, supplier_id: str) -> dict:
    name = next((s["name"] for s in workbench.data["suppliers"] if s["id"] == supplier_id), supplier_id)
    orders = []
    for entry in workbench.ledger.invoices(supplier_id=supplier_id):
        events = workbench.receiving.events_for_po(entry["po_number"])
        counted = sum(workbench.receiving.count_event(e["id"])["total"] for e in events) if events else None
        billed = sum(line["qty"] for line in entry["lines"])
        orders.append({"invoice": entry["id"], "bill_no": entry["bill_no"], "po": entry["po_number"], "billed": billed,
                       "counted": counted, "short": counted is not None and counted < billed})
    cases = [{"case": c.id, "bill_no": c.bill_no, "state": c.state, "cause": (c.diagnosis or {}).get("cause", "")}
             for c in workbench.cases.values() if c.supplier_id == supplier_id]
    return {"supplier_id": supplier_id, "name": name, "orders": orders,
            "short_orders": sum(1 for o in orders if o["short"]), "cases": cases}


def build_casefile(workbench, case) -> dict:
    return {
        "case": case.id, "bill_no": case.bill_no, "supplier_id": case.supplier_id, "po_number": case.po_number,
        "state": case.state, "status": case.status,
        "billed": (case.bill or {}).get("lines", [{}])[0].get("qty"), "counted": case.counter.get("total"),
        "diagnosis": case.diagnosis, "proposal": case.proposal, "decision": case.decision,
        "evidence_ids": sorted((case.investigation or {}).get("evidence", {})),
        "invoice_id": case.invoice_id, "dispute_ref": (case.dispute or {}).get("portal_ref", ""),
        "supplier_file": supplier_file(workbench, case.supplier_id),
        "policy_hash": workbench.policy.hash, "filed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def write_casefile(directory: Path, casefile: dict) -> tuple[Path, str]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{casefile['case']}.json"
    path.write_text(json.dumps(casefile, indent=1, sort_keys=True, default=str), encoding="utf-8")
    return path, sha256(json.loads(json.dumps(casefile, default=str)))
