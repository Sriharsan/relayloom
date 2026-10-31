"""Accounts payable agents: offline tests with fake model clients and the built in ledger."""
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from relayloom.ap.ledger import LocalLedger
from relayloom.ap.masking import find, mask
from relayloom.ap.matcher import match
from relayloom.ap.pipeline import Network, Workbench, hidden_text
from relayloom.ap.policy import POLICY_PATH, Refused, load_policy
from relayloom.ap.receipts import ReceiptChain, Signer, verify
from relayloom.ap.schema import Invalid, validate_bill

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DATA = json.loads((FIXTURES / "data.json").read_text(encoding="utf-8"))
CASES = {case["case"]: case for case in DATA["cases"]}


class FakeReader:
    """Returns the bill the fixture generator wrote, as a model would. Records what it was sent."""

    route = "fake"

    def __init__(self, delay=0.0, tamper=None):
        self.sent, self.delay, self.tamper, self.active, self.peak = [], delay, tamper, 0, 0
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
        bill = json.loads(json.dumps(case["expected_bill"]))
        if self.tamper:
            self.tamper(bill)
        return {"bill": validate_bill(bill), "model": "fake", "route": "fake", "seconds": 0.0, "response_id": "fake-1"}

    def draft_dispute(self, facts, key=""):
        return {"text": f"Bill {facts['bill_no']}: {facts['problems'][0]}", "model": "fake", "route": "fake",
                "seconds": 0.0, "response_id": "fake-2"}


class FakeCounter:
    def count(self, photo, prompt, key):
        case = next(c for c in DATA["cases"] if c["bill_no"] == key)
        return {"count": case["delivered_in_photo"], "prompt": prompt, "model": "fake-sam", "route": "fake",
                "infer_seconds": 0.0}


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
        self.ledger.seed(DATA["suppliers"], DATA["purchase_orders"])
        self.checker = self.ledger  # same database, separate calls; ERPNext runs use a second client
        self.portal = FakePortal()

    def tearDown(self):
        self.ledger.db.close()
        self.folder.cleanup()

    def bench(self, reader=None):
        network = Network(self.ledger)
        return Workbench(self.policy, self.ledger, self.checker, self.chain, reader or FakeReader(), FakeCounter(),
                         network, FIXTURES, DATA, portal=self.portal)

    # schema
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

    # masking
    def test_masking_removes_gstin_bank_ifsc_phone_and_email(self):
        text = (FIXTURES / "bills" / "VEL-2611.txt").read_text(encoding="utf-8")
        masked, records = mask(text)
        self.assertEqual(find(masked), [])
        self.assertEqual({r["kind"] for r in records}, {"gstin", "ifsc", "phone", "email", "bank_account"})
        for value in ("33AAZFV1234K1Z5", "50100012345678", "SYNT0000101", "98400 11223", "velantin.example"):
            self.assertNotIn(value, masked)
        self.assertIn("VEL-2611", masked)
        self.assertNotIn("50100012345678", json.dumps(records))

    # matcher
    def test_matcher_tolerances(self):
        po = next(p for p in DATA["purchase_orders"] if p["po_number"] == "PO-1001")
        bill = CASES["match"]["expected_bill"]
        self.assertTrue(match(po, bill, {"TIN-15L": 24}, self.policy.limits)["matched"])
        short = match(po, bill, {"TIN-15L": 23}, self.policy.limits)
        self.assertFalse(short["matched"])
        self.assertIn("counted 23, billed 24", short["problems"][0])
        within = json.loads(json.dumps(bill))
        within["lines"][0]["rate_inr"] = 411.0  # 0.24 percent, inside the 0.5 percent tolerance
        within["lines"][0]["amount_inr"] = 24 * 411.0
        within["tax_inr"] = round(24 * 411.0 * 0.18, 2)
        within["total_inr"] = round(24 * 411.0 * 1.18, 2)
        self.assertTrue(match(po, within, {"TIN-15L": 24}, self.policy.limits)["matched"])
        big = dict(self.policy.limits, owner_amount_limit_inr=1000)
        self.assertTrue(match(po, bill, {"TIN-15L": 24}, big)["over_limit"])

    # policy
    def test_policy_levels_and_refusals(self):
        self.assertEqual(self.policy.level("enter_matching_bill"), "run_alone")
        self.assertEqual(self.policy.level("send_dispute"), "run_with_approval")
        with self.assertRaises(Refused):
            self.policy.require("send_dispute")
        with self.assertRaises(Refused):
            self.policy.require("change_bank_from_invoice_text", approved=True)
        bad = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        bad["operations"]["send_dispute"]["level"] = "run_alone"
        (self.root / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_policy(self.root / "bad.json")

    # cases
    def test_matching_bill_is_entered_and_checked_alone(self):
        bench = self.bench()
        [case] = bench.run_batch([CASES["match"]])
        self.assertEqual(case.state, "entered_checked", case.status)
        self.assertEqual(case.readback["differences"], [])
        self.assertEqual(case.pay_to["source"], "ledger supplier master")
        self.assertEqual(self.ledger.count_invoices("SUP-VELAN", "VEL-2611"), 1)

    def test_short_delivery_waits_for_owner_and_dispute_needs_approval(self):
        bench = self.bench()
        [case] = bench.run_batch([CASES["short"]])
        self.assertEqual(case.state, "held_for_owner")
        self.assertEqual(case.proposal["action"], "send_dispute")
        self.assertIn("counted 34, billed 40", case.proposal["reason"])
        self.assertIsNone(self.ledger.find_invoice("SUP-PON", "PON-0457"))
        self.assertTrue(case.dispute["text"])
        self.assertEqual(self.portal.sent, [])
        with self.assertRaises(Refused):
            bench.send_dispute(case)
        bench.decide(case.id, "approve", "Owner")
        self.assertEqual(case.state, "dispute_sent")
        self.assertEqual(self.portal.sent, ["short"])
        self.assertIsNone(self.ledger.find_invoice("SUP-PON", "PON-0457"))

    def test_price_mismatch_rejected_by_owner_changes_nothing(self):
        bench = self.bench()
        [case] = bench.run_batch([CASES["price"]])
        self.assertIn("rate 18.50, PO rate 16.00", case.proposal["reason"])
        bench.decide(case.id, "reject", "Owner")
        self.assertEqual(case.state, "closed_by_owner")
        self.assertEqual(self.portal.sent, [])
        with self.assertRaises(Refused):
            bench.decide(case.id, "approve", "Owner")

    def test_injection_is_recorded_and_payment_uses_master_data(self):
        self.assertTrue(hidden_text(FIXTURES / "bills" / "VEL-2614.pdf"))
        reader = FakeReader()
        bench = self.bench(reader)
        [case] = bench.run_batch([CASES["injection"]])
        self.assertTrue(case.injection["hidden_text"])
        self.assertNotIn("99887766554433", reader.sent[0])
        self.assertNotIn("99887766554433", json.dumps(case.view()))
        self.assertEqual(case.state, "entered_checked")
        self.assertEqual(case.pay_to["account_last4"], "5678")
        steps = [r["body"]["step"] for r in self.chain.read("injection")]
        self.assertIn("injection_check", steps)

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
        self.assertTrue(any("qty" in d for d in case.readback["differences"]))

    def test_offline_hold_and_reconnect_without_duplicate(self):
        bench = self.bench()
        records = [CASES["netcut-1"], CASES["netcut-2"], CASES["netcut-3"]]

        def cut_after_first(case):
            # The ledger accepted the first invoice, then the link dropped before the readback.
            if not bench.network.online:
                return
            bench.network.cut()

        bench.after_create = cut_after_first
        bench.pool._max_workers = 1
        cases = bench.run_batch(records)
        states = [case.state for case in cases]
        self.assertEqual(states, ["held_offline"] * 3)
        self.assertEqual(sum(self.ledger.count_invoices(c.supplier_id, c.bill_no) for c in cases), 1)
        self.assertTrue(all(case.bill for case in cases))  # reading continued while offline
        bench.after_create = None
        bench.reconnect()
        self.assertEqual([case.state for case in cases], ["entered_checked"] * 3)
        for case in cases:
            self.assertEqual(self.ledger.count_invoices(case.supplier_id, case.bill_no), 1)
        bench.reconnect()  # a second reconnect has nothing queued and creates nothing
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

    def test_receipts_verify_offline_and_detect_tampering(self):
        bench = self.bench()
        bench.run_batch([CASES["match"], CASES["short"]])
        receipts = self.chain.read()
        ok, problems = verify(receipts, self.signer.public_key)
        self.assertTrue(ok, problems)
        self.assertTrue(all(r["body"]["policy_hash"] == self.policy.hash for r in receipts))
        receipts[2]["body"]["decision"] = "something else"
        ok, problems = verify(receipts, self.signer.public_key)
        self.assertFalse(ok)
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
        self.assertIn("supplier:SUP-VELAN", bench.locks)
        self.assertIn("po:PO-1001", bench.locks)


if __name__ == "__main__":
    unittest.main()
