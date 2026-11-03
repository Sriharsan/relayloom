"""The likely cause of a mismatch, with the reasons behind it.

Like a note in a patient file, it says what is probably wrong, who is probably responsible, how sure the records
let us be, and what to do next. It is plain code over the evidence the Investigator already collected. Every
reason cites evidence ids, and the same check that guards the findings (every citation exists, every number is in
the cited record) must pass. If it does not, or the records do not point one way, the cause is "unclear" and a
person decides. It never accuses a person: "responsible" names a party or says nobody can tell yet.
"""
from __future__ import annotations

import re

from .investigator import verify_finding

CAUSES = {
    "short_delivery": ("Short delivery", "the supplier shipped less than it billed",
                       "Ask the supplier for a credit note or a corrected bill for the quantity received."),
    "duplicate_bill": ("Duplicate bill", "the supplier billed twice, or our own books already hold this bill",
                       "Reject the duplicate and keep the first bill."),
    "price_above_order": ("Price above the order", "the supplier charged more than the agreed order price",
                          "Ask the supplier for a corrected bill at the order price."),
    "count_unreliable": ("The two counts disagree", "the receiving count cannot be trusted yet",
                         "Recount the delivery with a person before paying or disputing."),
    "unclear": ("Unclear", "nobody can tell yet", "A person reviews the evidence."),
}


def _first(evidence: dict, prefix: str):
    return next((k for k in evidence if k.startswith(prefix)), None)


def diagnose(evidence: dict, checks: dict, match: dict, proposal: dict) -> dict:
    bill_id, po_id = _first(evidence, "BILL:"), _first(evidence, "PO:")
    has_recount = "CALC:recount" in evidence
    row = (match or {}).get("rows", [{}])[0] if (match or {}).get("rows") else {}
    because: list[dict] = []
    cause, confidence = "unclear", "low"

    duplicate = next((k for k, v in evidence.items() if v["kind"] == "invoice" and "is in the books:" in v["text"]), None)
    shortfalls = [k for k, v in evidence.items() if v["kind"] == "invoice" and re.search(r"for PO-\d+: [\d.]+ billed$", v["text"])]
    differing = [k for k, v in evidence.items() if v["kind"] == "recount" and v.get("first") != v.get("second")]
    received, billed = checks.get("goods_received"), checks.get("billed")
    owed = (received or 0) - (checks.get("billed_before") or 0)

    if checks.get("duplicate_bill") and duplicate:
        cause, confidence = "duplicate_bill", "high"
        because.append({"text": "This bill has the same supplier, amount and date as a bill already in the books.",
                        "cites": [bill_id, duplicate]})
    elif has_recount and not checks.get("recount_agree"):
        cause, confidence = "count_unreliable", "low"
        because.append({"text": "Counting the same photos with a second wording gave a different total than the first count.",
                        "cites": ["CALC:recount", *differing]})
    elif billed is not None and billed > owed and received is not None:
        cause = "short_delivery"
        confidence = "high" if has_recount and checks.get("recount_agree") else "medium"
        because.append({"text": f"The goods received on the order ({received}) do not cover this bill ({billed:g}).",
                        "cites": ["CALC:received"]})
        if has_recount:
            because.append({"text": "Two independent counts of every photo agree, so the count is reliable.",
                            "cites": ["CALC:recount"]})
        if shortfalls:
            because.append({"text": "This supplier has fallen short on an earlier order too.", "cites": shortfalls})
    elif any("rate" in p for p in (match or {}).get("problems", [])) and row:
        cause, confidence = "price_above_order", "high"
        because.append({"text": f"The bill rate is {row['bill_rate']:.2f} and the order rate is {row['po_rate']:.2f}.",
                        "cites": [bill_id, po_id]})
    else:
        problems = "; ".join((match or {}).get("problems", [])) or "the records show a mismatch without a single clear cause"
        because.append({"text": "The records do not point to one cause.", "cites": [bill_id] if bill_id else []})
        because[0]["problems"] = problems

    ok, problems = verify_finding([{"text": b["text"], "cites": b["cites"]} for b in because], evidence)
    if not ok:  # a diagnosis that cannot show its sources is never shown as a cause
        cause, confidence = "unclear", "low"
        because = [{"text": "The records do not point to one cause.", "cites": [bill_id] if bill_id else []}]
    label, responsible, next_step = CAUSES[cause]
    return {"cause": cause, "label": label, "responsible": responsible, "confidence": confidence,
            "because": [{"text": b["text"], "cites": b["cites"]} for b in because], "next_step": next_step,
            "verified": ok, "problems": problems if not ok else [], "proposal_action": (proposal or {}).get("action", "")}
