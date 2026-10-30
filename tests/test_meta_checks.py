"""Refusal paths for the live Meta check. FAKE transports only: no provider calls."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from relayloom.controller import Rejected
from relayloom.meta import ENDPOINT, MetaWorker, REQUIRED_ENVIRONMENT, SYNTHETIC_BRIEF

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_meta", ROOT / "scripts" / "check_meta.py")
check_meta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_meta)

FAKE_KEY = "FAKE-KEY-for-offline-tests-0000"  # Not a credential. Never sent anywhere.


def fake_meta_transport(request, timeout):
    """FAKE provider. Echoes the required evidence with fixed usage."""
    payload = json.loads(request.data)
    evidence = json.loads(payload["messages"][1]["content"])
    return {"model": payload["model"], "choices": [{"finish_reason": "stop", "message": {
        "role": "assistant", "content": json.dumps({"summary": "FAKE transport summary", **evidence["required_evidence"]})}}],
        "usage": {"prompt_tokens": 90, "completion_tokens": 30, "total_tokens": 120}}


def must_not_send(request, timeout):
    raise AssertionError("A refusal path attempted to dispatch a request.")


class MetaCheckTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.env = {"MODEL_API_KEY": FAKE_KEY, "RELAYLOOM_META_ENDPOINT": ENDPOINT,
                    "RELAYLOOM_META_MODEL": "muse-spark-1.3", "RELAYLOOM_SYNTHETIC_ONLY": "I_CONFIRM_SYNTHETIC_DATA",
                    "RELAYLOOM_META_LEDGER": str(Path(self.folder.name) / "ledger.sqlite3")}

    def tearDown(self):
        self.folder.cleanup()

    def test_check_refuses_without_explicit_credit_flag(self):
        lines = []
        with patch.object(check_meta, "run_checks", side_effect=AssertionError("must not run")):
            code = check_meta.main([], env=self.env, send=must_not_send, out=lines.append)
        self.assertEqual(code, 2)
        self.assertTrue(lines[0].startswith("REFUSED"))
        self.assertFalse(Path(self.env["RELAYLOOM_META_LEDGER"]).exists())

    def test_missing_configuration_names_variables_never_values(self):
        for name in REQUIRED_ENVIRONMENT:
            partial = {key: value for key, value in self.env.items() if key != name}
            with self.assertRaises(ValueError) as caught:
                MetaWorker.from_environment(partial)
            message = str(caught.exception)
            self.assertIn(name, message)
            self.assertNotIn(FAKE_KEY, message)
            self.assertNotIn(self.env["RELAYLOOM_META_LEDGER"], message)
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError) as caught:
            MetaWorker.from_environment()
        self.assertIn("MODEL_API_KEY", str(caught.exception))

    def test_server_refuses_meta_mode_without_key(self):
        from relayloom import __main__ as entry
        lines = []
        with patch.dict(os.environ, {}, clear=True), patch("sys.argv", ["relayloom", "--enable-meta-synthetic"]), \
                patch("sys.stderr") as stderr, self.assertRaises(SystemExit) as caught:
            stderr.write.side_effect = lines.append
            entry.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("MODEL_API_KEY", "".join(lines))

    def test_key_never_appears_in_repr_or_delivery_errors(self):
        def leaking_fake_transport(request, timeout):
            raise RuntimeError("FAKE provider error echoing " + request.headers["Authorization"])
        worker = MetaWorker(endpoint=ENDPOINT, model="muse-spark-1.3", api_key=FAKE_KEY,
                            ledger_path=self.env["RELAYLOOM_META_LEDGER"], send=leaking_fake_transport)
        self.assertNotIn(FAKE_KEY, repr(worker))
        with self.assertRaises(Rejected) as caught:
            worker.execute("leak:1:product", "leak", "product",
                           {"brief": SYNTHETIC_BRIEF, "audience": "Customers", "refund_days": 30}, {})
        self.assertNotIn(FAKE_KEY, str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)

    def test_check_cases_pass_with_fake_transport_and_dispatch_once(self):
        lines, sent = [], []
        def counting_fake(request, timeout):
            sent.append(1)
            return fake_meta_transport(request, timeout)
        code = check_meta.main(["--i-have-credit"], env=self.env, send=counting_fake, out=lines.append)
        self.assertEqual(code, 0, "\n".join(lines))
        self.assertEqual(len(sent), 1)
        self.assertTrue(all(line.startswith("PASS") for line in lines[:-1]))
        self.assertFalse(any(FAKE_KEY in line for line in lines))

    def test_check_reports_fail_without_dispatch_when_key_missing(self):
        lines = []
        env = {key: value for key, value in self.env.items() if key != "MODEL_API_KEY"}
        code = check_meta.main(["--i-have-credit"], env=env, send=must_not_send, out=lines.append)
        self.assertEqual(code, 1)
        self.assertTrue(any(line.startswith("FAIL  environment configured") for line in lines))

    def test_attempt_ledger_cap_refuses_further_dispatch(self):
        sent = []
        def counting_fake(request, timeout):
            sent.append(1)
            return fake_meta_transport(request, timeout)
        worker = MetaWorker(endpoint=ENDPOINT, model="muse-spark-1.3", api_key=FAKE_KEY,
                            ledger_path=self.env["RELAYLOOM_META_LEDGER"], max_attempts=1, send=counting_fake)
        intent = {"brief": SYNTHETIC_BRIEF, "audience": "Customers", "refund_days": 30}
        worker.execute("cap:1:product", "cap", "product", intent, {})
        with self.assertRaises(Rejected) as caught:
            worker.execute("cap:2:product", "cap", "product", intent, {})
        self.assertEqual(caught.exception.status, 429)
        self.assertEqual(len(sent), 1)


if __name__ == "__main__":
    unittest.main()
