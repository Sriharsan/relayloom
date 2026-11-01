"""The Investigator: works on every mismatch before a person sees it.

It recounts from every photo, adds up all receiving events on the purchase order, checks the bill against the PO
price and the last price paid, looks for a duplicate bill, and looks at the supplier's past shortfalls. Every fact
becomes an evidence item with an id. The finding is a list of statements that each cite those ids. Code checks that
every cited id exists, and that every number in a statement appears in the evidence it cites, before the finding is
shown. Then it proposes an action; the policy decides what happens next.
"""
from __future__ import annotations

import re

CITE = re.compile(r"[A-Z]+:[A-Za-z0-9._-]+")
NUMBER = re.compile(r"\d+(?:\.\d+)?")


class Evidence:
    def __init__(self):
        self.items: dict[str, dict] = {}

    def add(self, evidence_id: str, kind: str, text: str, **data) -> str:
        self.items[evidence_id] = {"id": evidence_id, "kind": kind, "text": text, **data}
        return evidence_id

    def listing(self) -> str:
        return "\n".join(f"[{item['id']}] {item['text']}" for item in self.items.values())


def verify_finding(statements: list[dict], evidence: dict[str, dict]) -> tuple[bool, list[str]]:
    """Every statement must cite something; every citation must exist; every number must come from a cited item."""
    problems = []
    if not statements:
        problems.append("the finding has no statements")
    for index, statement in enumerate(statements, start=1):
        cites = statement.get("cites") or []
        text = statement.get("text", "")
        if not cites:
            problems.append(f"statement {index} cites nothing")
        for cite in cites + CITE.findall(text):
            if cite not in evidence:
                problems.append(f"statement {index} cites {cite}, which is not a record")
        sources = " ".join(evidence[c]["text"] for c in cites if c in evidence)
        numbers_in_sources = set(NUMBER.findall(sources.replace(",", "")))
        for number in NUMBER.findall(CITE.sub("", text).replace(",", "")):
            if number not in numbers_in_sources and number.rstrip("0").rstrip(".") not in numbers_in_sources:
                problems.append(f"statement {index} says {number}, which its cited records do not show")
    return not problems, problems


def rupees(value) -> str:
    return f"{float(value):.2f}"


class Investigator:
    def __init__(self, receiving, ledger, writer=None):
        self.receiving, self.ledger, self.writer = receiving, ledger, writer

    def investigate(self, case_id: str, bill: dict, po: dict, match_result: dict, event_ids: list[str],
                    allow_recount: bool = True) -> dict:
        evidence, statements = Evidence(), []
        line = bill["lines"][0]
        item = line["item_code"]
        po_line = next(i for i in po["items"] if i["item_code"] == item)
        bill_id = evidence.add(f"BILL:{bill['bill_no']}", "bill",
                               f"Bill {bill['bill_no']} from {bill['supplier_id']} dated {bill['bill_date']}: {line['qty']:g} "
                               f"{line['description']} at {rupees(line['rate_inr'])}, total {rupees(bill['total_inr'])}, "
                               f"cites purchase order {bill['po_number']}")
        po_id = evidence.add(f"PO:{po['po_number']}", "po",
                             f"Purchase order {po['po_number']} orders {po_line['qty']:g} {po_line['description']} at "
                             f"{rupees(po_line['rate_inr'])}")

        # 1. Goods: every receiving event on this order, every unique photo, duplicates dropped.
        received = self.receiving.received_for_po(po["po_number"])
        photo_ids, event_cites, recount_agree, recounts = [], [], True, []
        for event in received["events"]:
            rows = []
            for photo in event["photos"]:
                if photo["counted"]:
                    pid = evidence.add(f"PHOTO:{photo['photo']}", "photo",
                                       f"Photo {photo['photo']}: {photo['count']} counted by SAM 3.1 with the prompt "
                                       f"'{photo['prompt']}'", photo=photo["photo"], overlay=photo.get("overlay", ""),
                                       count=photo["count"])
                    rows.append(pid)
                else:
                    pid = evidence.add(f"PHOTO:{photo['photo']}", "photo",
                                       f"Photo {photo['photo']} is a duplicate of {photo['duplicate_of']} "
                                       f"(similarity {photo['similarity']}) and was not counted", photo=photo["photo"])
                    rows.append(pid)
            photo_ids += rows
            eid = evidence.add(f"REC:{event['event_id']}", "receiving",
                               f"Receiving event {event['event_id']} on {event['date']}: {event['total']} counted over "
                               f"{event['unique_photos']} unique photos, {event['duplicate_photos']} duplicate photos ignored")
            event_cites.append(eid)
        parts = " + ".join(f"{e['total']} in {e['event_id']}" for e in received["events"])
        calc = evidence.add("CALC:received", "calc", f"Goods received in total on {po['po_number']}: {received['total']} "
                            f"({parts}); the bill says {line['qty']:g}")
        statements.append({"text": f"The dock received {received['total']} in total on {po['po_number']} across "
                                   f"{len(received['events'])} receiving events, while the bill says {line['qty']:g}.",
                           "cites": [bill_id, calc, *event_cites]})
        for event in received["events"]:
            for photo in event["photos"]:
                if not photo["counted"]:
                    statements.append({"text": f"Photo {photo['photo']} repeats {photo['duplicate_of']} and was counted once.",
                                       "cites": [f"PHOTO:{photo['photo']}", f"PHOTO:{photo['duplicate_of']}"]})
        if allow_recount:
            for event in received["events"]:
                again = self.receiving.recount_event(event["event_id"])
                recounts.append(again)
                recount_agree = recount_agree and again["agree"]
                for row in again["photos"]:
                    evidence.add(f"RECOUNT:{row['photo']}", "recount",
                                 f"Recount of {row['photo']} with the prompt '{row['prompt']}': {row['second']} against "
                                 f"{row['first']} the first time", photo=row["photo"], first=row["first"], second=row["second"])
            cites = [f"RECOUNT:{r['photo']}" for again in recounts for r in again["photos"]]
            total_second = sum(a["total_second"] for a in recounts)
            cites.append(evidence.add("CALC:recount", "calc", f"Recount total over all unique photos: {total_second}; "
                                      f"first count total: {received['total']}"))
            statements.append({"text": ("An independent recount of every photo agrees: " if recount_agree else
                                        "An independent recount of the photos disagrees with the first count: ") +
                                       f"{total_second} against {received['total']}.", "cites": cites})

        # 2. Running total on the order: what was billed before.
        earlier = self.ledger.invoices(po_number=po["po_number"])
        earlier = [e for e in earlier if e["bill_no"] != bill["bill_no"]]
        billed_before = 0
        for entry in earlier:
            qty = sum(l["qty"] for l in entry["lines"] if l["item_code"] == item)
            billed_before += qty
            evidence.add(f"INV:{entry['id']}", "invoice", f"Invoice {entry['id']} (bill {entry['bill_no']}, {entry['bill_date']}) "
                         f"already in the books for {po['po_number']}: {qty:g} at {rupees(entry['lines'][0]['rate_inr'])}, "
                         f"total {rupees(entry['total_inr'])}", qty=qty)
        if earlier:
            calc_billed = evidence.add("CALC:billed_before", "calc", f"Already billed on {po['po_number']} before this bill: {billed_before:g}")
            statements.append({"text": f"{billed_before:g} on {po['po_number']} was already billed before this bill.",
                               "cites": [calc_billed, *[f"INV:{e['id']}" for e in earlier]]})
        else:
            statements.append({"text": f"No earlier bill on {po['po_number']} is in the books.", "cites": [po_id]})

        # 3. Price against the order and the last price paid.
        history = [e for e in self.ledger.invoices(supplier_id=bill["supplier_id"]) if e["bill_no"] != bill["bill_no"]
                   and any(l["item_code"] == item for l in e["lines"])]
        last = history[0] if history else None
        price_cites = [bill_id, po_id]
        text = f"The bill rate is {rupees(line['rate_inr'])} and the order rate is {rupees(po_line['rate_inr'])}"
        if last:
            last_rate = next(l["rate_inr"] for l in last["lines"] if l["item_code"] == item)
            evidence.add(f"INV:{last['id']}", "invoice", f"Invoice {last['id']} (bill {last['bill_no']}, {last['bill_date']}) "
                         f"in the books for {last['po_number']}: {sum(l['qty'] for l in last['lines'] if l['item_code'] == item):g} at "
                         f"{rupees(last_rate)}, total {rupees(last['total_inr'])}")
            price_cites.append(f"INV:{last['id']}")
            text += f"; the last price paid was {rupees(last_rate)}."
        else:
            text += "; there is no earlier price paid in the books."
        statements.append({"text": text, "cites": price_cites})

        # 4. Duplicate bill: same supplier, same number, or same amount and date under another number.
        duplicate = next((e for e in self.ledger.invoices(supplier_id=bill["supplier_id"])
                          if e["bill_no"] != bill["bill_no"] and abs(e["total_inr"] - bill["total_inr"]) < 0.01
                          and e["bill_date"] == bill["bill_date"] and e["lines"][0]["item_code"] == item), None)
        if duplicate:
            evidence.add(f"INV:{duplicate['id']}", "invoice", f"Invoice {duplicate['id']} (bill {duplicate['bill_no']}, "
                         f"{duplicate['bill_date']}) is in the books: {duplicate['lines'][0]['qty']:g} at "
                         f"{rupees(duplicate['lines'][0]['rate_inr'])}, total {rupees(duplicate['total_inr'])}")
            statements.append({"text": f"This bill has the same supplier, amount {rupees(bill['total_inr'])} and date as "
                                       f"bill {duplicate['bill_no']}, which is already in the books.",
                               "cites": [bill_id, f"INV:{duplicate['id']}"]})

        # 5. The supplier's past shortfalls: earlier orders where the dock counted less than was billed.
        shortfalls = []
        for entry in self.ledger.invoices(supplier_id=bill["supplier_id"]):
            if entry["po_number"] == po["po_number"]:
                continue
            events = self.receiving.events_for_po(entry["po_number"])
            if not events:
                continue
            counted = sum(self.receiving.count_event(e["id"])["total"] for e in events)
            billed = sum(l["qty"] for l in entry["lines"])
            if counted < billed:
                evidence.add(f"INV:{entry['id']}", "invoice", f"Invoice {entry['id']} (bill {entry['bill_no']}, {entry['bill_date']}) "
                             f"for {entry['po_number']}: {billed:g} billed")
                rec = [evidence.add(f"REC:{e['id']}", "receiving", f"Receiving event {e['id']} on {e['date']}: "
                                    f"{self.receiving.count_event(e['id'])['total']} counted") for e in events]
                shortfalls.append({"invoice": entry["id"], "billed": billed, "counted": counted, "events": rec})
                statements.append({"text": f"On {entry['po_number']} this supplier billed {billed:g} and the dock counted "
                                           f"{counted}.", "cites": [f"INV:{entry['id']}", *rec]})
        if not shortfalls:
            statements.append({"text": f"No earlier shortfall for {bill['supplier_id']} is in the records.", "cites": [bill_id]})

        proposal = self.propose(bill, po_line, line, received, billed_before, duplicate, recount_agree, match_result, statements)
        checks = {"goods_received": received["total"], "billed": line["qty"], "billed_before": billed_before,
                  "recount_agree": recount_agree, "duplicate_bill": bool(duplicate), "past_shortfalls": len(shortfalls)}
        template = {"statements": statements, "route": "template (code wrote the statements from the evidence)",
                    "model": "", "seconds": 0.0, "response_id": "", "written_by": "template"}
        finding = self.write(case_id, evidence, template)
        return {"evidence": evidence.items, "finding": finding, "proposal": proposal, "checks": checks,
                "received": received, "recounts": recounts, "billed_before": billed_before}

    def write(self, case_id: str, evidence: Evidence, template: dict) -> dict:
        """Let the model write the finding when one is wired in; only a verified finding is ever shown."""
        ok, problems = verify_finding(template["statements"], evidence.items)
        template["verified"], template["problems"] = ok, problems
        if not self.writer:
            return template
        try:
            reply = self.writer.write_finding(evidence.listing(), key=case_id)
            statements = [{"text": s["text"], "cites": list(s["cites"])} for s in reply["statements"]]
        except Exception as error:  # a model that cannot answer never blocks the case
            template["model_error"] = f"{type(error).__name__}: {str(error)[:120]}"
            return template
        verified, model_problems = verify_finding(statements, evidence.items)
        if verified:
            return {"statements": statements, "verified": True, "problems": [], "written_by": "model",
                    "model": reply["model"], "route": reply["route"], "seconds": reply["seconds"],
                    "response_id": reply["response_id"], "template_statements": template["statements"]}
        template["model_rejected"] = {"problems": model_problems[:6], "statements": statements}
        return template

    @staticmethod
    def propose(bill, po_line, line, received, billed_before, duplicate, recount_agree, match_result, statements) -> dict:
        problems = match_result["problems"]
        if duplicate:
            return {"action": "reject_duplicate", "operation": "hold_bill",
                    "reason": f"duplicate of bill {duplicate['bill_no']} already in the books"}
        if not recount_agree:
            return {"action": "hold_for_recount", "operation": "hold_bill",
                    "reason": "the independent recount does not agree with the first count; a person should count"}
        owed = received["total"] - billed_before
        if line["qty"] > owed:
            short = line["qty"] - owed
            return {"action": "send_dispute", "operation": "send_dispute",
                    "reason": f"{short:g} billed but not received; ask for a credit note or a corrected bill for {owed:g}",
                    "received_quantity": owed}
        if any("rate" in p for p in problems):
            return {"action": "send_dispute", "operation": "send_dispute",
                    "reason": f"bill rate {rupees(line['rate_inr'])} is above the order rate {rupees(po_line['rate_inr'])}"}
        return {"action": "send_dispute", "operation": "send_dispute", "reason": "; ".join(problems)}
