"""The agents: Intake, Reader, Counter, Matcher, Clerk, Checker, Disputer. One case per bill.

Agents act alone where the policy says run_alone. Everything else waits for the owner.
Each step writes a signed receipt. A batch runs in parallel with locks per supplier and PO.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import threading
import time

from . import i18n
from .casefile import build_casefile, supplier_file, supplier_patterns, write_casefile
from .diagnosis import diagnose
from .ledger import LedgerOffline
from .investigator import Investigator
from .masking import find, mask
from .matcher import match
from .receiving import Receiving
from .policy import Policy, Refused
from .receipts import ReceiptChain, sha256

STEPS = ("read", "count", "match", "investigate", "enter", "check")
INJECTION_HINTS = re.compile(r"(ignore|update|change|new)\b.{0,40}\b(bank|account|ifsc)|for the ai|assistant processing", re.I)


class Network:
    """The link between the agents and anything that changes the books or leaves the building."""

    def __init__(self, *links):
        self.links = list(links)
        self.online = True
        self.changed = threading.Condition()

    def cut(self):
        with self.changed:
            self.online = False
            for link in self.links:
                link.online = False
            self.changed.notify_all()

    def restore(self):
        with self.changed:
            self.online = True
            for link in self.links:
                link.online = True
            self.changed.notify_all()


class Case:
    def __init__(self, record: dict, fixtures: Path):
        self.id = record["case"]
        self.record = record
        self.bill_no = record["bill_no"]
        self.supplier_id = record["supplier_id"]
        self.po_number = record["po_number"]
        self.bill_pdf = fixtures / record["bill_pdf"]
        self.bill_text_path = fixtures / record["bill_text"]
        self.state = "queued"
        self.status = "Queued"
        self.steps = {step: {"state": "waiting", "seconds": None, "note": ""} for step in STEPS}
        self.masked_text = ""
        self.masks: list[dict] = []
        self.injection: dict | None = None
        self.bill: dict | None = None
        self.reader: dict = {}
        self.counter: dict = {}
        self.event_ids: list[str] = record.get("event_ids", [])
        self.investigation: dict | None = None
        self.match: dict | None = None
        self.proposal: dict | None = None
        self.decision: dict | None = None
        self.invoice_id = ""
        self.readback: dict | None = None
        self.pay_to: dict | None = None
        self.dispute: dict | None = None
        self.queued_action: str = ""
        self.ledger_name = ""
        self.diagnosis: dict | None = None
        self.casefile: dict | None = None

    def view(self) -> dict:
        return {"id": self.id, "bill_no": self.bill_no, "supplier_id": self.supplier_id, "po_number": self.po_number,
                "state": self.state, "status": self.status, "steps": self.steps, "masked_text": self.masked_text,
                "masks": self.masks, "injection": self.injection, "bill": self.bill, "reader": self.reader,
                "counter": self.counter, "investigation": self.investigation, "event_ids": self.event_ids,
                "match": self.match, "proposal": self.proposal, "decision": self.decision,
                "invoice_id": self.invoice_id, "readback": self.readback, "pay_to": self.pay_to,
                "dispute": self.dispute, "queued_action": self.queued_action, "ledger": self.ledger_name,
                "diagnosis": self.diagnosis, "casefile": self.casefile,
                }


class Workbench:
    def __init__(self, policy: Policy, ledger, checker_ledger, chain: ReceiptChain, reader, counter,
                 network: Network, fixtures: Path, data: dict, portal=None, owner: str = "Owner", goods: bool = True):
        self.policy, self.ledger, self.checker_ledger = policy, ledger, checker_ledger
        self.chain, self.reader, self.counter, self.network = chain, reader, counter, network
        self.fixtures, self.data, self.portal, self.owner = fixtures, data, portal, owner
        self.goods = goods  # False is the paperwork only baseline used by the benchmark
        self.receiving = Receiving(data, counter, fixtures)
        self.investigator = Investigator(self.receiving, ledger, writer=reader if getattr(reader, "writes_findings", False) else None)
        self.cases: dict[str, Case] = {}
        self.lock = threading.RLock()
        self.locks: dict[str, threading.Lock] = {}
        self.pool = ThreadPoolExecutor(max_workers=policy.limits["parallel_cases"], thread_name_prefix="case")
        self.after_create = None  # test and demo hook: called after the ledger accepted an invoice
        self.casefile_dir = None  # when set, every finished case is filed here and the file's hash is receipted
        self.notify = None  # optional: notify(kind, title, body, case) puts an alert on the phone page

    # Intake -------------------------------------------------------------
    def intake(self, record: dict) -> Case:
        case = Case(record, self.fixtures)
        with self.lock:
            self.cases[case.id] = case
        self.receipt(case, "Intake", "intake", "accepted", input_hash=sha256(case.bill_pdf.read_bytes()),
                     detail={"bill": case.bill_pdf.name, "receiving_events": case.event_ids})
        return case

    def run_batch(self, records: list[dict]) -> list[Case]:
        cases = [self.intake(record) for record in records]
        futures = [self.pool.submit(self.process, case) for case in cases]
        for future in futures:
            future.result()
        return cases

    def submit(self, records: list[dict]) -> list[Case]:
        cases = [self.intake(record) for record in records]
        for case in cases:
            self.pool.submit(self.process, case)
        return cases

    def resource_lock(self, key: str) -> threading.Lock:
        with self.lock:
            return self.locks.setdefault(key, threading.Lock())

    def alert(self, case: Case, kind: str, key: str, **params):
        """Raise an alert. The words live in strings.json so the phone can show them in English, Tamil or Hindi."""
        if self.notify:
            try:
                made = i18n.alert(kind, key, **params)
                self.notify(kind, made["title"], made["body"], case.id, key, made["params"])
            except Exception:  # an alert that cannot be sent never stops the case
                pass

    def receipt(self, case: Case, agent: str, step: str, decision: str, **fields):
        return self.chain.append(case.id, agent, step, decision, **fields)

    def mark(self, case: Case, step: str, state: str, seconds=None, note=""):
        case.steps[step] = {"state": state, "seconds": seconds, "note": note}

    # The run ------------------------------------------------------------
    def process(self, case: Case):
        try:
            self._read(case)
            self._count(case)
            self._match(case)
            if case.state == "matched":
                with self.resource_lock("supplier:" + case.supplier_id), self.resource_lock("po:" + case.po_number):
                    self.enter(case)
        except Exception as error:  # A failed step stops the case and says why. No automatic retry.
            case.state, case.status = "failed", f"Stopped: {type(error).__name__}: {str(error)[:160]}"
            self.receipt(case, "Workbench", "stopped", "failed", detail={"error": str(error)[:300]})

    def _read(self, case: Case):
        self.policy.require("read_bill")
        self.mark(case, "read", "running")
        case.status = "Reading the bill"
        text = case.bill_text_path.read_text(encoding="utf-8")
        hidden = hidden_text(case.bill_pdf)
        case.masked_text, case.masks = mask(text)
        leftover = find(case.masked_text)
        if leftover:
            raise Refused(f"masking left {leftover} in the text; nothing sent")
        self.receipt(case, "Reader", "mask", "masked", input_hash=sha256(text.encode()),
                     detail={"masks": case.masks, "masked_sha256": sha256(case.masked_text.encode())})
        suspicious = [line for line in hidden + text.splitlines() if INJECTION_HINTS.search(line)]
        if hidden or suspicious:
            masked_lines = [mask(line)[0] for line in (hidden or suspicious)]
            case.injection = {"hidden_text": bool(hidden), "lines": masked_lines,
                              "action": "ignored: bank details come only from the ledger supplier master"}
            self.receipt(case, "Reader", "injection_check", "attempt_recorded",
                         detail={"hidden_white_text": bool(hidden), "lines": masked_lines})
            self.alert(case, "injection", "a.injection", bill=case.bill_no)
        result = self.reader.read_bill(case.masked_text, key=case.bill_no)
        case.bill = result["bill"]
        case.reader = {"model": result["model"], "route": result["route"], "seconds": result["seconds"],
                       "response_id": result["response_id"], "usage": result.get("usage", {})}
        self.mark(case, "read", "done", result["seconds"], result["route"])
        self.receipt(case, "Reader", "read", "extracted", input_hash=sha256(case.masked_text.encode()),
                     model=result["model"], route=result["route"], response_id=result["response_id"],
                     detail={"bill": case.bill, "seconds": result["seconds"], "usage": result.get("usage", {})})

    def _count(self, case: Case):
        self.policy.require("count_goods")
        if not self.goods:
            self.mark(case, "count", "skipped", None, "paperwork only")
            return
        self.mark(case, "count", "running")
        case.status = "Counting the delivery"
        received = self.receiving.received_for_po(case.po_number)
        for event in received["events"]:
            for photo in event["photos"]:
                if photo["counted"] and photo["count"] > self.policy.limits["max_count_per_photo"]:
                    raise Refused("more items in a photo than the counter is trusted for")
        photos = [p for e in received["events"] for p in e["photos"]]
        routes = sorted({p["route"] for p in photos if p["counted"]})
        case.counter = {"events": received["events"], "total": received["total"], "count": received["total"],
                        "seconds": received["seconds"], "route": "; ".join(routes), "model": "SAM 3.1",
                        "item_code": case.bill["lines"][0]["item_code"]}
        self.mark(case, "count", "done", received["seconds"], f"{received['total']} counted")
        for event in received["events"]:
            self.receipt(case, "Counter", "count", f"counted {event['total']} in {event['event_id']}",
                         input_hash=sha256([p["photo"] for p in event["photos"]]), model="SAM 3.1",
                         route="; ".join(sorted({p["route"] for p in event["photos"] if p["counted"]})),
                         detail={"event": event["event_id"], "date": event["date"], "total": event["total"],
                                 "photos": [{k: p.get(k) for k in ("photo", "count", "counted", "duplicate_of", "prompt", "seconds", "trace")}
                                            for p in event["photos"]]})

    def _match(self, case: Case):
        self.policy.require("match")
        case.status = "Matching"
        started = time.perf_counter()
        try:
            po = self.ledger.get_po(case.bill["po_number"])
            earlier = [e for e in self.ledger.invoices(po_number=case.bill["po_number"]) if e["bill_no"] != case.bill["bill_no"]]
        except LedgerOffline:
            po = next((p for p in self.data["purchase_orders"] if p["po_number"] == case.po_number), None)
            earlier = [{"lines": [{"item_code": h["item_code"], "qty": h["qty"]}]} for h in self.data["history_invoices"]
                       if h["po_number"] == case.po_number and h["bill_no"] != case.bill["bill_no"]]
        if po is None:
            raise Refused(f"no purchase order {case.bill['po_number']}")
        billed_before: dict[str, float] = {}
        for entry in earlier:
            for line in entry["lines"]:
                billed_before[line["item_code"]] = billed_before.get(line["item_code"], 0) + line["qty"]
        received = {case.counter["item_code"]: case.counter["total"]} if self.goods else None
        result = match(po, case.bill, received, billed_before, self.policy.limits)
        case.match = result
        seconds = round(time.perf_counter() - started, 3)
        self.mark(case, "match", "done" if result["matched"] else "held", seconds,
                  "matched" if result["matched"] else "; ".join(result["problems"]))
        self.receipt(case, "Matcher", "match", "matched" if result["matched"] else "mismatch",
                     input_hash=sha256({"po": po, "bill": case.bill, "received": received, "billed_before": billed_before}),
                     detail={"problems": result["problems"], "over_limit": result["over_limit"], "received": received,
                             "billed_before": billed_before})
        if result["matched"] and not result["over_limit"]:
            case.state = "matched"
            self.mark(case, "investigate", "skipped", None, "nothing to investigate")
            return
        if result["matched"]:
            case.proposal = {"action": "enter_bill", "operation": "enter_bill_over_limit",
                             "reason": f"total above the owner limit of Rs {self.policy.limits['owner_amount_limit_inr']:,}"}
            self.mark(case, "investigate", "skipped", None, "nothing to investigate")
        elif self.goods:
            self._investigate(case, po)
        else:
            case.proposal = {"action": "send_dispute", "operation": "send_dispute", "reason": "; ".join(result["problems"])}
            self.mark(case, "investigate", "skipped", None, "paperwork only")
        case.proposal["policy_level"] = self.policy.level(case.proposal["operation"])
        case.state, case.status = "held_for_owner", "Waiting for the owner"
        self.mark(case, "enter", "held", None, "needs the owner")
        self.receipt(case, "Matcher", "propose", f"held for owner: {case.proposal['action']}", detail=case.proposal)
        cause = (case.diagnosis or {}).get("label")
        cause_code = (case.diagnosis or {}).get("cause")
        self.alert(case, "needs_owner", "a.needs_owner", bill=case.bill_no, cause=cause or "", cause_key=f"d.{cause_code}" if cause_code else "",
                   reason=case.proposal["reason"])
        if case.proposal["action"] == "send_dispute" and self.goods:
            self.draft_dispute(case)

    def _investigate(self, case: Case, po: dict):
        self.policy.require("investigate_mismatch")
        self.mark(case, "investigate", "running")
        case.status = "Investigating"
        started = time.perf_counter()
        report = self.investigator.investigate(case.id, case.bill, po, case.match, case.event_ids)
        finding = report["finding"]
        case.investigation = {k: report[k] for k in ("evidence", "finding", "proposal", "checks")}
        case.investigation["recounts"] = report["recounts"]
        case.proposal = dict(report["proposal"])
        seconds = round(time.perf_counter() - started, 1)
        self.mark(case, "investigate", "done", seconds, case.proposal["reason"])
        self.receipt(case, "Investigator", "investigate", f"proposes {case.proposal['action']}",
                     input_hash=sha256(report["evidence"]), model=finding.get("model", ""),
                     route=finding.get("route", ""), response_id=finding.get("response_id", ""),
                     detail={"checks": report["checks"], "finding_verified": finding["verified"],
                             "written_by": finding["written_by"], "statements": finding["statements"],
                             "evidence_ids": sorted(report["evidence"]), "proposal": case.proposal,
                             "seconds": seconds})
        case.diagnosis = diagnose(report["evidence"], report["checks"], case.match, case.proposal)
        self.receipt(case, "Investigator", "diagnose", f"likely cause: {case.diagnosis['cause']}",
                     input_hash=sha256({"checks": report["checks"], "evidence": sorted(report["evidence"])}),
                     detail={k: case.diagnosis[k] for k in ("cause", "responsible", "confidence", "because", "next_step")})

    # Clerk and Checker --------------------------------------------------
    def entry(self, case: Case) -> dict:
        po = next(p for p in self.data["purchase_orders"] if p["po_number"] == case.po_number)
        return {"case": case.id, "supplier_id": case.bill["supplier_id"], "bill_no": case.bill["bill_no"],
                "bill_date": case.bill["bill_date"], "po_number": case.bill["po_number"], "lines": case.bill["lines"],
                "tax_inr": case.bill["tax_inr"], "total_inr": case.bill["total_inr"], "tax_rate": po["tax_rate"],
                "tax_account": self.data.get("tax_account", "")}

    def enter(self, case: Case, approved: bool = False):
        operation = "enter_matching_bill" if not approved else case.proposal["operation"]
        self.policy.require(operation, approved=approved)
        case.ledger_name = self.ledger.name
        if not self.network.online:
            self.hold_offline(case, "enter")
            return
        self.mark(case, "enter", "running")
        case.status = "Entering the bill"
        started = time.perf_counter()
        try:
            existing = self.ledger.find_invoice(case.bill["supplier_id"], case.bill["bill_no"])
            if existing:
                case.invoice_id = existing
                self.receipt(case, "Clerk", "enter", "already in ledger; not entered again",
                             ledger_readback=existing)
            else:
                case.invoice_id = self.ledger.create_invoice(self.entry(case))
                self.receipt(case, "Clerk", "enter", "entered", ledger_readback=case.invoice_id,
                             approver=case.decision["by"] if approved and case.decision else "",
                             detail={"ledger": self.ledger.name, "invoice": case.invoice_id})
                if self.after_create:
                    self.after_create(case)
        except LedgerOffline:
            self.hold_offline(case, "enter")
            return
        self.mark(case, "enter", "done", round(time.perf_counter() - started, 2), self.ledger.name)
        self.check(case)

    def check(self, case: Case):
        self.policy.require("check_readback")
        if not self.network.online:
            self.hold_offline(case, "check")
            return
        self.mark(case, "check", "running")
        case.status = "Checking the ledger"
        started = time.perf_counter()
        try:
            stored = self.checker_ledger.read_invoice(case.invoice_id)
            supplier = self.checker_ledger.get_supplier(case.bill["supplier_id"])
        except LedgerOffline:
            self.hold_offline(case, "check")
            return
        differences = compare(self.entry(case), stored)
        master = self.data_supplier(case.bill["supplier_id"])
        if supplier is None or supplier["bank_account"] != master["bank_account"] or supplier["ifsc"] != master["ifsc"]:
            differences.append("supplier master bank details are not the ones on record")
        case.readback = {"stored": stored, "differences": differences, "ledger": self.checker_ledger.name}
        seconds = round(time.perf_counter() - started, 2)
        if differences:
            case.state, case.status = "readback_failed", "Readback failed: not treated as entered"
            self.alert(case, "readback", "a.readback", bill=case.bill_no, differences="; ".join(differences))
            self.mark(case, "check", "failed", seconds, "; ".join(differences))
            self.receipt(case, "Checker", "check", "readback failed", ledger_readback=sha256(stored or {}),
                         detail={"differences": differences})
            return
        case.pay_to = {"source": "ledger supplier master", "account_last4": supplier["bank_account"][-4:],
                       "ifsc": supplier["ifsc"]}
        case.state, case.status = "entered_checked", "Entered and checked"
        self.mark(case, "check", "done", seconds, "every field matches")
        self.receipt(case, "Checker", "check", "entered and checked", ledger_readback=sha256(stored),
                     detail={"invoice": case.invoice_id, "pay_to": case.pay_to, "ledger": self.checker_ledger.name})
        self.file_case(case)

    def data_supplier(self, supplier_id: str) -> dict:
        return next(s for s in self.data["suppliers"] if s["id"] == supplier_id)

    # Offline hold and reconnect ----------------------------------------
    def hold_offline(self, case: Case, action: str):
        # change_books_while_offline is "never": the action is queued, not attempted.
        case.queued_action = action
        case.state, case.status = "held_offline", "Held, offline"
        self.alert(case, "offline", "a.offline", bill=case.bill_no)
        self.mark(case, action if action in STEPS else "enter", "held", None, "offline")
        self.receipt(case, "Clerk", action, "held offline; nothing entered or sent",
                     detail={"policy": "change_books_while_offline is never allowed"})

    def reconnect(self):
        """Ledger first, then each queued action once."""
        self.network.restore()
        self.policy.require("reconcile_after_reconnect")
        with self.lock:
            held = [case for case in self.cases.values() if case.state == "held_offline"]
        for case in held:
            action, case.queued_action = case.queued_action, ""
            with self.resource_lock("supplier:" + case.supplier_id), self.resource_lock("po:" + case.po_number):
                found = self.ledger.find_invoice(case.bill["supplier_id"], case.bill["bill_no"])
                self.receipt(case, "Clerk", "reconcile", "found in ledger" if found else "not in ledger",
                             ledger_readback=found or "")
                if action == "send_dispute":
                    case.state = "approved"
                    self.send_dispute(case)
                elif found:
                    case.invoice_id = found
                    self.mark(case, "enter", "done", None, "found after reconnect")
                    self.check(case)
                else:
                    self.enter(case, approved=bool(case.decision and case.decision["decision"] == "approve"))
        return held

    # Approvals and disputes --------------------------------------------
    def decide(self, case_id: str, decision: str, by: str) -> Case:
        case = self._decide(case_id, decision, by)
        if case.state in ("closed_by_owner", "dispute_sent"):
            self.file_case(case)
        return case

    def file_case(self, case: Case):
        """The Archivist: write the case file and put its hash in the receipt chain. Does nothing unless a folder is set."""
        if self.casefile_dir is None or (case.casefile and case.casefile["state"] == case.state):
            return
        casefile = build_casefile(self, case)
        path, digest = write_casefile(self.casefile_dir, casefile)
        case.casefile = {"state": case.state, "file": path.name, "sha256": digest}
        self.receipt(case, "Archivist", "file", f"case filed: {case.state}", input_hash=digest,
                     detail={"file": path.name, "cause": (case.diagnosis or {}).get("cause", ""),
                             "supplier_orders": len(casefile["supplier_file"]["orders"])})

    def supplier_file(self, supplier_id: str) -> dict:
        return supplier_file(self, supplier_id)

    def supplier_patterns(self, min_short: int = 2) -> dict:
        return supplier_patterns(self, min_short)

    def _decide(self, case_id: str, decision: str, by: str) -> Case:
        case = self.cases[case_id]
        if case.state != "held_for_owner" or decision not in ("approve", "reject"):
            raise Refused("this case is not waiting for a decision")
        case.decision = {"decision": decision, "by": by, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                         "action": case.proposal["action"], "policy_hash": self.policy.hash}
        self.receipt(case, "Owner", "decision", decision, approver=by, detail=case.decision)
        if decision == "reject":
            case.state, case.status = "closed_by_owner", "Rejected by the owner: nothing entered or sent"
            self.mark(case, "enter", "skipped", None, "owner rejected")
            return case
        case.state = "approved"
        action = case.proposal["action"]
        if action == "enter_bill":
            self.enter(case, approved=True)
        elif action == "send_dispute":
            self.send_dispute(case)
        else:  # reject_duplicate and hold_for_recount change nothing in the books and send nothing
            self.policy.require("hold_bill")
            case.state = "closed_by_owner"
            case.status = ("Duplicate bill rejected: nothing entered" if action == "reject_duplicate"
                           else "Held for a person to recount: nothing entered")
            self.mark(case, "enter", "skipped", None, case.status)
            self.receipt(case, "Owner", "close", case.status, approver=by, detail={"action": action})
        return case

    def draft_dispute(self, case: Case):
        facts = dispute_facts(self.data_supplier(case.supplier_id)["name"], case.bill_no, case.po_number, case.match,
                              case.investigation)
        result = self.reader.draft_dispute(facts, key=case.bill_no)
        case.dispute = {"text": result["text"], "model": result["model"], "route": result["route"],
                        "seconds": result["seconds"], "response_id": result["response_id"], "sent": False,
                        "form_filled_by": ""}
        self.receipt(case, "Disputer", "draft", "drafted", input_hash=sha256(facts), model=result["model"],
                     route=result["route"], response_id=result["response_id"],
                     detail={"seconds": result["seconds"], "text_sha256": sha256(result["text"].encode())})

    def send_dispute(self, case: Case):
        self.policy.require("send_dispute", approved=bool(case.decision and case.decision["decision"] == "approve"))
        if not self.network.online or self.portal is None:
            self.hold_offline(case, "send_dispute")
            return
        case.status = "Sending the dispute"
        result = self.portal.submit(case)
        case.dispute.update({"sent": True, "portal_ref": result["reference"], "form_filled_by": result["filled_by"],
                             "screenshot": result.get("screenshot", ""), "seconds_to_send": result["seconds"]})
        case.state, case.status = "dispute_sent", "Dispute sent to the supplier; bill not entered"
        self.mark(case, "enter", "skipped", None, "not entered: dispute sent")
        self.receipt(case, "Disputer", "send", "sent", approver=case.decision["by"],
                     ledger_readback=result["reference"], detail={k: v for k, v in result.items() if k != "screenshot"})


def dispute_facts(supplier_name: str, bill_no: str, po_number: str, match_result: dict, investigation: dict | None = None) -> dict:
    """The only facts the Disputer may use. No bank details, no free text from the bill."""
    row = match_result["rows"][0]
    facts = {"supplier": supplier_name, "bill_no": bill_no, "po_number": po_number, "item": row["description"],
             "ordered": row["po_qty"], "billed": row["bill_qty"], "received_in_total": row["received"],
             "billed_before_on_this_order": row["billed_before"], "po_rate": row["po_rate"],
             "billed_rate": row["bill_rate"], "problems": match_result["problems"],
             "ask": "send a credit note or a corrected bill for what was received, at the order rate"}
    if investigation:
        facts["recount_agrees"] = investigation["checks"]["recount_agree"]
        facts["past_shortfalls_for_this_supplier"] = investigation["checks"]["past_shortfalls"]
    return facts


def compare(expected: dict, stored: dict | None) -> list[str]:
    if stored is None:
        return ["invoice not found on readback"]
    differences = []
    for key in ("supplier_id", "bill_no", "bill_date", "po_number"):
        if str(stored.get(key)) != str(expected[key]):
            differences.append(f"{key}: ledger has {stored.get(key)!r}, expected {expected[key]!r}")
    stored_lines = {line["item_code"]: line for line in stored.get("lines", [])}
    for line in expected["lines"]:
        got = stored_lines.get(line["item_code"])
        if not got:
            differences.append(f"{line['item_code']} missing in ledger")
            continue
        for key in ("qty", "rate_inr", "amount_inr"):
            if abs(float(got[key]) - float(line[key])) > 0.01:
                differences.append(f"{line['item_code']} {key}: ledger {got[key]}, expected {line[key]}")
    if len(stored_lines) != len(expected["lines"]):
        differences.append("ledger has a different number of lines")
    for key in ("tax_inr", "total_inr"):
        if abs(float(stored.get(key, 0)) - float(expected[key])) > 1.0:
            differences.append(f"{key}: ledger {stored.get(key)}, expected {expected[key]}")
    return differences


def hidden_text(pdf: Path) -> list[str]:
    """Text a person cannot see on the printed bill: white or near white, or tiny."""
    try:
        import fitz
    except ImportError:
        return []
    found = []
    with fitz.open(pdf) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        colour = span["color"]
                        white = all(((colour >> shift) & 255) > 235 for shift in (16, 8, 0))
                        if span["text"].strip() and (white or span["size"] < 5):
                            found.append(span["text"].strip())
    return found
