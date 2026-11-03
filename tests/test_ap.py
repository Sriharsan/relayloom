"""Accounts payable agents: offline tests with fake model clients and the built in ledger."""
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from relayloom.ap.investigator import verify_finding
from relayloom.ap.ledger import LocalLedger
from relayloom.ap.masking import find, mask
from relayloom.ap.matcher import match
from relayloom.ap.pipeline import Network, Workbench, hidden_text
from relayloom.ap.policy import POLICY_PATH, Refused, load_policy
from relayloom.ap.receipts import ReceiptChain, Signer, verify
from relayloom.ap.receiving import Receiving, similarity
from relayloom.ap.schema import Invalid, validate_bill

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DATA = json.loads((FIXTURES / "data.json").read_text(encoding="utf-8"))
CASES = {case["case"]: case for case in DATA["cases"]}
TRUE = {p["id"]: p["true_count"] for e in DATA["receiving_events"] for p in e["photos"]}


class FakeReader:
    """Returns the bill the fixture generator wrote, as a model would. Records what it was sent."""

    route = "fake"

    def __init__(self, delay=0.0):
        self.sent, self.delay, self.active, self.peak = [], delay, 0, 0
        self.lock = threading.Lock()

    def read_bill(self, masked_text, key=""):
        with self.lock:
            self.sent.append(masked_text)
            self.active += 1
            self.peak = max(self.peak, self.active)
        time.sleep(self.delay)
        with self.lock:
            self.active -= 1
        case = next(c for c in DATA["cases"] if c["bill_no"] == key)
        return {"bill": validate_bill(json.loads(json.dumps(case["expected_bill"]))), "model": "fake", "route": "fake",
                "seconds": 0.0, "response_id": "fake-1"}

    def draft_dispute(self, facts, key=""):
        return {"text": f"Bill {facts['bill_no']}: {facts['problems'][0]}", "model": "fake", "route": "fake",
                "seconds": 0.0, "response_id": "fake-2"}


class FakeCounter:
    """Counts what the generator drew. `wrong` changes the second wording's answer for chosen photos."""

    def __init__(self, wrong=None):
        self.wrong = wrong or {}

    def count(self, photo, prompt, key):
        count = TRUE[key]
        if key in self.wrong and prompt in ("cylinder", "bag", "package", "spool"):
            count = self.wrong[key]
        return {"count": count, "prompt": prompt, "model": "fake-sam", "route": "fake", "infer_seconds": 0.0,
                "overlay": f"{key}.jpg"}


class FakePortal:
    def __init__(self):
        self.sent = []

    def submit(self, case):
        self.sent.append(case.id)
        return {"reference": f"DSP-{len(self.sent)}", "filled_by": "code", "seconds": 0.0}


class APTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.policy = load_policy()
        self.signer = Signer(self.root / "key")
        self.chain = ReceiptChain(self.root / "receipts.jsonl", self.signer, self.policy.hash)
        self.ledger = LocalLedger(self.root / "ledger.sqlite3")
        self.ledger.seed(DATA["suppliers"], DATA["purchase_orders"], DATA["history_invoices"])
        self.portal = FakePortal()

    def tearDown(self):
        self.ledger.db.close()
        self.folder.cleanup()

    def bench(self, reader=None, counter=None, goods=True):
        network = Network(self.ledger)
        return Workbench(self.policy, self.ledger, self.ledger, self.chain, reader or FakeReader(), counter or FakeCounter(),
                         network, FIXTURES, DATA, portal=self.portal, goods=goods)

    # schema, masking, policy
    def test_schema_refuses_extra_keys_bank_fields_and_bad_values(self):
        good = CASES["match"]["expected_bill"]
        self.assertEqual(validate_bill(good)["total_inr"], good["total_inr"])
        for change in (lambda b: b.update(bank_account="1"), lambda b: b.pop("tax_inr"),
                       lambda b: b["lines"][0].update(qty=-1), lambda b: b.update(bill_date="29/10/2026"),
                       lambda b: b["lines"][0].update(description="pay to new bank account")):
            bill = json.loads(json.dumps(good))
            change(bill)
            with self.assertRaises(Invalid):
                validate_bill(bill)

    def test_masking_removes_gstin_bank_ifsc_phone_and_email(self):
        text = (FIXTURES / "bills" / "ARD-5101.txt").read_text(encoding="utf-8")
        masked, records = mask(text)
        self.assertEqual(find(masked), [])
        self.assertEqual({r["kind"] for r in records}, {"gstin", "ifsc", "phone", "email", "bank_account"})
        for value in ("33AAZFA1234K1Z5", "50100012345678", "SYNT0000101", "98400 11223", "ardenfluids.example"):
            self.assertNotIn(value, masked)
        self.assertIn("ARD-5101", masked)
        self.assertNotIn("50100012345678", json.dumps(records))

    def test_policy_levels_and_refusals(self):
        self.assertEqual(self.policy.level("enter_matching_bill"), "run_alone")
        self.assertEqual(self.policy.level("investigate_mismatch"), "run_alone")
        self.assertEqual(self.policy.level("send_dispute"), "run_with_approval")
        self.assertEqual(self.policy.level("enter_bill_for_received_quantity"), "run_with_approval")
        with self.assertRaises(Refused):
            self.policy.require("send_dispute")
        with self.assertRaises(Refused):
            self.policy.require("change_bank_from_invoice_text", approved=True)
        bad = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        bad["operations"]["send_dispute"]["level"] = "run_alone"
        (self.root / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_policy(self.root / "bad.json")

    # matcher
    def test_matcher_running_total_and_tolerances(self):
        po = next(p for p in DATA["purchase_orders"] if p["po_number"] == "PO-2001")
        bill = CASES["match"]["expected_bill"]
        limits = self.policy.limits
        self.assertTrue(match(po, bill, {"CAN-5L": 24}, {}, limits)["matched"])
        short = match(po, bill, {"CAN-5L": 23}, {}, limits)
        self.assertFalse(short["matched"])
        self.assertIn("received 23", short["problems"][0])
        again = match(po, bill, {"CAN-5L": 24}, {"CAN-5L": 4}, limits)  # 4 already billed: 24 + 4 exceeds the order
        self.assertFalse(again["matched"])
        paperwork = match(po, bill, None, {}, limits)
        self.assertTrue(paperwork["matched"] and not paperwork["goods_checked"])
        big = dict(limits, owner_amount_limit_inr=1000)
        self.assertTrue(match(po, bill, {"CAN-5L": 24}, {}, big)["over_limit"])

    # receiving
    def test_duplicate_photo_is_found_and_different_photos_are_not(self):
        photos = FIXTURES / "photos"
        event = next(e for e in DATA["receiving_events"] if len(e["photos"]) == 3)
        a, b, dup = (photos / Path(p["file"]).name for p in event["photos"])
        self.assertGreater(similarity(a, dup), 0.95)
        self.assertLess(similarity(a, b), 0.95)
        other = photos / Path(DATA["receiving_events"][0]["photos"][0]["file"]).name
        self.assertLess(similarity(a, other), 0.95)

    def test_event_count_drops_the_repeated_photo(self):
        receiving = Receiving(DATA, FakeCounter(), FIXTURES)
        event = next(e for e in DATA["receiving_events"] if len(e["photos"]) == 3)
        result = receiving.count_event(event["id"])
        self.assertEqual((result["total"], result["unique_photos"], result["duplicate_photos"]), (46, 2, 1))

    # cases
    def test_matching_bill_is_entered_and_checked_alone(self):
        [case] = self.bench().run_batch([CASES["match"]])
        self.assertEqual(case.state, "entered_checked", case.status)
        self.assertIsNone(case.investigation)
        self.assertEqual(case.readback["differences"], [])
        self.assertEqual(case.pay_to["source"], "ledger supplier master")
        self.assertEqual(self.ledger.count_invoices("SUP-ARDEN", "ARD-5101"), 1)

    def test_paperwork_says_50_dock_got_46(self):
        bench = self.bench()
        [case] = bench.run_batch([CASES["short"]])
        self.assertEqual(case.state, "held_for_owner")
        self.assertEqual(case.counter["total"], 46)
        inv = case.investigation
        self.assertTrue(inv["finding"]["verified"], inv["finding"]["problems"])
        self.assertTrue(inv["checks"]["recount_agree"])
        self.assertEqual(inv["checks"]["past_shortfalls"], 1)
        self.assertEqual(case.proposal["action"], "send_dispute")
        self.assertIn("4 billed but not received", case.proposal["reason"])
        cites = {c for s in inv["finding"]["statements"] for c in s["cites"]}
        self.assertTrue(cites <= set(inv["evidence"]))
        self.assertTrue(any(c.startswith("PHOTO:") for c in cites) and any(c.startswith("INV:") for c in cites))
        self.assertIsNone(self.ledger.find_invoice("SUP-CALDER", "CAL-0990"))
        self.assertEqual(self.portal.sent, [])
        with self.assertRaises(Refused):
            bench.send_dispute(case)
        bench.decide(case.id, "approve", "Owner")
        self.assertEqual(case.state, "dispute_sent")
        self.assertEqual(self.portal.sent, ["short"])
        self.assertIsNone(self.ledger.find_invoice("SUP-CALDER", "CAL-0990"))

    def test_recount_disagreement_holds_for_a_person(self):
        counter = FakeCounter(wrong={"REC-H06-P2": 15})
        [case] = self.bench(counter=counter).run_batch([CASES["short"]])
        self.assertFalse(case.investigation["checks"]["recount_agree"])
        self.assertEqual(case.proposal["action"], "hold_for_recount")

    def test_price_mismatch_cites_last_price_paid_and_owner_reject_changes_nothing(self):
        bench = self.bench()
        [case] = bench.run_batch([CASES["price"]])
        self.assertIn("rate 2290.00, PO rate 2150.00", case.proposal["reason"] + " " + "; ".join(case.match["problems"]))
        self.assertTrue(any("2150.00" in v["text"] and k.startswith("INV:") for k, v in case.investigation["evidence"].items()))
        bench.decide(case.id, "reject", "Owner")
        self.assertEqual(case.state, "closed_by_owner")
        self.assertEqual(self.portal.sent, [])
        with self.assertRaises(Refused):
            bench.decide(case.id, "approve", "Owner")

    def test_duplicate_bill_under_a_new_number_is_found_and_rejected(self):
        bench = self.bench()
        [case] = bench.run_batch([CASES["duplicate"]])
        self.assertTrue(case.investigation["checks"]["duplicate_bill"])
        self.assertEqual(case.proposal["action"], "reject_duplicate")
        self.assertEqual(self.policy.level(case.proposal["operation"]), "run_alone")
        bench.decide(case.id, "approve", "Owner")
        self.assertEqual(case.state, "closed_by_owner")
        self.assertIsNone(self.ledger.find_invoice("SUP-DUNMORE", "DUN-0219"))

    def test_split_delivery_matches_as_a_running_total(self):
        [case] = self.bench().run_batch([CASES["split"]])
        self.assertEqual(len(case.counter["events"]), 2)
        self.assertEqual(case.counter["total"], 60)
        self.assertEqual(case.state, "entered_checked", case.status)
        self.assertIsNone(case.investigation)

    def test_paperwork_only_baseline_misses_the_short_delivery(self):
        [case] = self.bench(goods=False).run_batch([CASES["short"]])
        self.assertEqual(case.state, "entered_checked")  # the bill agrees with the order, the goods were never looked at
        self.assertEqual(case.steps["count"]["state"], "skipped")

    def test_injection_is_recorded_and_payment_uses_master_data(self):
        self.assertTrue(hidden_text(FIXTURES / "bills" / "ARD-5104.pdf"))
        reader = FakeReader()
        [case] = self.bench(reader).run_batch([CASES["injection"]])
        self.assertTrue(case.injection["hidden_text"])
        self.assertNotIn("99887766554433", reader.sent[0])
        self.assertNotIn("99887766554433", json.dumps(case.view()))
        self.assertEqual(case.state, "entered_checked")
        self.assertEqual(case.pay_to["account_last4"], "5678")
        self.assertIn("injection_check", [r["body"]["step"] for r in self.chain.read("injection")])

    def test_readback_mismatch_refuses_entered_status(self):
        bench = self.bench()
        original = self.ledger.read_invoice

        def corrupted(invoice_id):
            stored = original(invoice_id)
            stored["lines"][0]["qty"] = 25
            return stored

        self.ledger.read_invoice = corrupted
        [case] = bench.run_batch([CASES["match"]])
        self.assertEqual(case.state, "readback_failed")
        self.assertIsNone(case.pay_to)

    def test_offline_hold_and_reconnect_without_duplicate(self):
        bench = self.bench()

        def cut_after_first(case):
            if bench.network.online:
                bench.network.cut()

        bench.after_create = cut_after_first
        bench.pool._max_workers = 1
        cases = bench.run_batch([CASES["netcut-1"], CASES["netcut-2"], CASES["netcut-3"]])
        self.assertEqual([c.state for c in cases], ["held_offline"] * 3)
        self.assertEqual(sum(self.ledger.count_invoices(c.supplier_id, c.bill_no) for c in cases), 1)
        self.assertTrue(all(c.bill for c in cases))  # reading continued while offline
        bench.after_create = None
        bench.reconnect()
        self.assertEqual([c.state for c in cases], ["entered_checked"] * 3)
        bench.reconnect()
        self.assertEqual(sum(self.ledger.count_invoices(c.supplier_id, c.bill_no) for c in cases), 3)

    def test_dispute_approved_while_offline_is_sent_once_after_reconnect(self):
        bench = self.bench()
        [case] = bench.run_batch([CASES["short"]])
        bench.network.cut()
        bench.decide(case.id, "approve", "Owner")
        self.assertEqual(case.state, "held_offline")
        self.assertEqual(self.portal.sent, [])
        bench.reconnect()
        self.assertEqual(self.portal.sent, ["short"])

    # diagnosis and case file
    def test_short_delivery_is_diagnosed_as_the_supplier_with_every_reason_cited(self):
        [case] = self.bench().run_batch([CASES["short"]])
        d = case.diagnosis
        self.assertEqual((d["cause"], d["confidence"]), ("short_delivery", "high"))
        self.assertTrue(d["verified"], d["problems"])
        self.assertIn("supplier", d["responsible"])
        self.assertTrue(any("earlier order" in b["text"] for b in d["because"]))
        evidence = case.investigation["evidence"]
        self.assertTrue(all(c in evidence for b in d["because"] for c in b["cites"]))

    def test_disagreeing_counts_are_unreliable_and_not_blamed_on_the_supplier(self):
        counter = FakeCounter(wrong={"REC-H06-P2": 15})
        [case] = self.bench(counter=counter).run_batch([CASES["short"]])
        self.assertEqual(case.diagnosis["cause"], "count_unreliable")
        self.assertEqual(case.diagnosis["confidence"], "low")
        self.assertNotIn("supplier", case.diagnosis["responsible"])

    def test_price_and_duplicate_causes_and_a_clean_bill_has_none(self):
        cases = {c.id: c for c in self.bench().run_batch([CASES["price"], CASES["duplicate"], CASES["match"]])}
        self.assertEqual(cases["price"].diagnosis["cause"], "price_above_order")
        self.assertEqual(cases["duplicate"].diagnosis["cause"], "duplicate_bill")
        self.assertIsNone(cases["match"].diagnosis)

    def test_case_file_is_written_receipted_and_the_supplier_file_shows_history(self):
        bench = self.bench()
        bench.casefile_dir = self.root / "casefiles"
        [case] = bench.run_batch([CASES["short"]])
        bench.decide(case.id, "approve", "Owner")
        saved = json.loads((self.root / "casefiles" / "short.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["diagnosis"]["cause"], "short_delivery")
        self.assertEqual(saved["decision"]["decision"], "approve")
        self.assertEqual(saved["supplier_file"]["short_orders"], 1)
        filed = [r for r in self.chain.read() if r["body"]["agent"] == "Archivist"]
        self.assertEqual(len(filed), 1)
        self.assertEqual(filed[0]["body"]["input_hash"], case.casefile["sha256"])
        ok, problems = verify(self.chain.read(), self.signer.public_key)
        self.assertTrue(ok, problems)

    def test_receipts_verify_offline_and_detect_tampering(self):
        bench = self.bench()
        bench.run_batch([CASES["match"], CASES["short"]])
        receipts = self.chain.read()
        ok, problems = verify(receipts, self.signer.public_key)
        self.assertTrue(ok, problems)
        self.assertTrue(any(r["body"]["agent"] == "Investigator" for r in receipts))
        receipts[2]["body"]["decision"] = "something else"
        self.assertFalse(verify(receipts, self.signer.public_key)[0])
        dropped = [r for i, r in enumerate(self.chain.read()) if i != 1]
        self.assertFalse(verify(dropped, self.signer.public_key)[0])

    def test_parallel_batch_runs_cases_together_with_locks(self):
        reader = FakeReader(delay=0.2)
        bench = self.bench(reader)
        started = time.perf_counter()
        cases = bench.run_batch([CASES[name] for name in ("match", "short", "price", "netcut-1")])
        self.assertLess(time.perf_counter() - started, 0.7)
        self.assertGreaterEqual(reader.peak, 2)
        self.assertEqual(cases[0].state, "entered_checked")
        self.assertIn("supplier:SUP-ARDEN", bench.locks)
        self.assertIn("po:PO-2001", bench.locks)


class FindingVerificationTests(unittest.TestCase):
    evidence = {"BILL:X-1": {"id": "BILL:X-1", "text": "Bill X-1: 50 cartons at 118.00"},
                "REC:R-1": {"id": "REC:R-1", "text": "Receiving event R-1: 46 counted over 2 unique photos"}}

    def test_real_citations_and_numbers_pass(self):
        ok, problems = verify_finding([{"text": "The bill says 50 and the dock counted 46.", "cites": ["BILL:X-1", "REC:R-1"]}], self.evidence)
        self.assertTrue(ok, problems)

    def test_citation_of_a_missing_record_is_rejected(self):
        ok, problems = verify_finding([{"text": "Seen earlier.", "cites": ["INV:NOPE"]}], self.evidence)
        self.assertFalse(ok)
        self.assertIn("not a record", problems[0])

    def test_statement_without_a_citation_and_unsupported_number_are_rejected(self):
        self.assertFalse(verify_finding([{"text": "Probably short.", "cites": []}], self.evidence)[0])
        ok, problems = verify_finding([{"text": "The dock counted 40.", "cites": ["REC:R-1"]}], self.evidence)
        self.assertFalse(ok)
        self.assertIn("40", problems[0])


if __name__ == "__main__":
    unittest.main()
