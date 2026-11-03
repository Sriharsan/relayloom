"""The relayloom command line: check, verify, and the refusal paths. SAM is replaced by a fake so no model is needed."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from relayloom import cli

BILL = {"supplier_id": "SUP-CALDER", "bill_no": "CAL-1", "bill_date": "2026-11-01", "po_number": "PO-1",
        "lines": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0, "amount_inr": 5900.0}],
        "tax_inr": 1062.0, "total_inr": 6962.0}
PO = {"po_number": "PO-1", "supplier_id": "SUP-CALDER", "tax_rate": 0.18,
      "items": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0}]}


class FakeSam:
    def __init__(self, n):
        self.n = n

    def count(self, photo, prompt, key):
        return {"count": self.n, "infer_seconds": 0.1}


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / "bill.json").write_text(json.dumps(BILL), encoding="utf-8")
        (self.dir / "po.json").write_text(json.dumps(PO), encoding="utf-8")
        (self.dir / "dock").mkdir()
        (self.dir / "dock" / "a.jpg").write_bytes(bytes([0xFF, 0xD8, 0xFF]))
        patch = mock.patch.object(cli, "HOME", self.dir / "home")
        patch.start()
        self.addCleanup(patch.stop)

    def run_check(self, counted):
        argv = ["check", "--bill-json", str(self.dir / "bill.json"), "--po", str(self.dir / "po.json"), "--photos", str(self.dir / "dock"),
                "--words", "cardboard box", "--out", str(self.dir / "out")]
        with mock.patch.object(cli, "build_sam", lambda: FakeSam(counted)), contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, out.getvalue()

    def test_a_short_delivery_is_held_and_the_receipts_verify(self):
        code, out = self.run_check(46)
        self.assertEqual(code, 3)
        self.assertIn("HELD", out)
        with contextlib.redirect_stdout(io.StringIO()) as verified:
            self.assertEqual(cli.main(["verify", str(self.dir / "out" / "receipts.jsonl")]), 0)
        self.assertIn("chain verified", verified.getvalue())

    def test_a_full_delivery_is_clear(self):
        code, out = self.run_check(50)
        self.assertEqual(code, 0)
        self.assertIn("CLEAR TO ENTER", out)

    def test_an_edited_receipt_breaks_the_chain(self):
        self.run_check(46)
        path = self.dir / "out" / "receipts.jsonl"
        text = path.read_text(encoding="utf-8").replace("counted 46", "counted 50")
        path.write_text(text, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as verified:
            self.assertEqual(cli.main(["verify", str(path)]), 1)
        self.assertIn("BROKEN", verified.getvalue())

    def test_missing_photos_stop_with_a_clear_message(self):
        with self.assertRaises(SystemExit) as stopped:
            cli.expand_photos([str(self.dir / "nothing.jpg")])
        self.assertIn("not found", str(stopped.exception))

    def test_models_pull_needs_the_users_own_token_and_prints_nothing_secret(self):
        with mock.patch.dict("os.environ", {"HF_TOKEN": ""}), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(["models", "pull"]), 2)
        self.assertIn("HF_TOKEN", out.getvalue())


if __name__ == "__main__":
    unittest.main()
