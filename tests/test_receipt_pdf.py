"""The PDF receipt: made offline, plain words, and honest about a changed chain."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import fitz

from relayloom import cli

BILL = {"supplier_id": "SUP-CALDER", "bill_no": "CAL-1", "bill_date": "2026-11-01", "po_number": "PO-1",
        "lines": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0, "amount_inr": 5900.0}],
        "tax_inr": 1062.0, "total_inr": 6962.0}
PO = {"po_number": "PO-1", "supplier_id": "SUP-CALDER", "tax_rate": 0.18,
      "items": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0}]}


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = cli.main(list(argv))
    return code, out.getvalue()


class ReceiptPdfTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "bill.json").write_text(json.dumps(BILL), encoding="utf-8")
        (self.dir / "po.json").write_text(json.dumps(PO), encoding="utf-8")
        code, _ = run("check", "--bill-json", str(self.dir / "bill.json"), "--po", str(self.dir / "po.json"), "--counted", "46", "--out", str(self.dir / "out"))
        self.assertIn(code, (0, 3))
        self.receipts = self.dir / "out" / "receipts.jsonl"

    def test_a_receipt_file_becomes_a_readable_pdf(self):
        pdf = self.dir / "receipt.pdf"
        code, text = run("receipt", str(self.receipts), "--out", str(pdf))
        self.assertEqual(code, 0, text)
        self.assertIn("signatures verified", text)
        words = "".join(page.get_text() for page in fitz.open(pdf))
        self.assertIn("Delivery check receipt", words)
        self.assertIn("Every step is signed", words)

    def test_evidence_photos_are_attached_and_the_pdf_stays_readable(self):
        import cv2
        import numpy as np
        photo = self.dir / "dock.jpg"
        cv2.imwrite(str(photo), (np.random.rand(240, 320, 3) * 255).astype("uint8"))
        pdf = self.dir / "with_photo.pdf"
        code, text = run("receipt", str(self.receipts), "--out", str(pdf), "--evidence", str(photo))
        self.assertEqual(code, 0, text)
        self.assertIn("1 evidence photos", text)
        doc = fitz.open(pdf)
        self.assertEqual(len({img[0] for page in doc for img in page.get_images()}), 1)
        self.assertIn("dock.jpg", "".join(page.get_text() for page in doc))

    def test_a_changed_receipt_is_reported_as_not_verified(self):
        self.receipts.write_text(self.receipts.read_text(encoding="utf-8").replace("46", "50", 1), encoding="utf-8")
        code, text = run("receipt", str(self.receipts), "--out", str(self.dir / "r.pdf"))
        self.assertEqual(code, 1)
        self.assertIn("NOT verified", text)


class DamagedGoodsTests(unittest.TestCase):
    def test_damaged_units_do_not_count_as_received_and_the_bill_is_held_with_a_plain_reason(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "bill.json").write_text(json.dumps(BILL), encoding="utf-8")
        (folder / "po.json").write_text(json.dumps(PO), encoding="utf-8")
        code, text = run("check", "--bill-json", str(folder / "bill.json"), "--po", str(folder / "po.json"), "--counted", "50", "--damaged", "6", "--out", str(folder / "out"))
        self.assertEqual(code, 3, text)
        self.assertIn("6 of 50 damaged", text)
        self.assertIn("credit note or a replacement", text)
        lines = (folder / "out" / "receipts.jsonl").read_text(encoding="utf-8")
        self.assertIn("condition", lines)

    def test_clean_delivery_with_no_damage_is_unchanged(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "bill.json").write_text(json.dumps(BILL), encoding="utf-8")
        (folder / "po.json").write_text(json.dumps(PO), encoding="utf-8")
        code, _ = run("check", "--bill-json", str(folder / "bill.json"), "--po", str(folder / "po.json"), "--counted", "50", "--out", str(folder / "out"))
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
