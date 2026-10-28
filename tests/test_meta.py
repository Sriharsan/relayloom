"""All Meta transport is replaced by local functions. No provider calls."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from relayloom.controller import Controller, Rejected, task_input
from relayloom.meta import AttemptLedger, ENDPOINT, MetaWorker, SYNTHETIC_BRIEF


def response_for(request, timeout):
    payload = json.loads(request.data)
    evidence = json.loads(payload["messages"][1]["content"])
    return {"model": payload["model"], "choices": [{"finish_reason": "stop", "message": {
        "role": "assistant", "content": json.dumps({"summary": "Synthetic model fixture", **evidence["required_evidence"]})}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140}}


class MetaTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.intent = {"brief": SYNTHETIC_BRIEF, "audience": "Customers", "refund_days": 30}

    def tearDown(self):
        self.folder.cleanup()

    def worker(self, send=response_for, **kwargs):
        return MetaWorker(endpoint=ENDPOINT, model="muse-spark-1.3", api_key="synthetic-test-key", ledger_path=self.root / "usage.sqlite3", send=send, **kwargs)

    def test_environment_requires_explicit_synthetic_opt_in(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                MetaWorker.from_environment()
        with patch.dict(os.environ, {"RELAYLOOM_SYNTHETIC_ONLY": "I_CONFIRM_SYNTHETIC_DATA",
                                    "RELAYLOOM_META_ENDPOINT": ENDPOINT,
                                    "RELAYLOOM_META_MODEL": "muse-spark-1.3",
                                    "MODEL_API_KEY": "synthetic-test-key", "RELAYLOOM_META_LEDGER": str(self.root / "env.sqlite3")}, clear=True):
            self.assertEqual(MetaWorker.from_environment().mode, "meta")

    def test_unreviewed_destination_model_or_unbounded_config_refused(self):
        base = dict(endpoint=ENDPOINT, model="muse-spark-1.3", api_key="synthetic-test-key", ledger_path=self.root / "config.sqlite3")
        for change in ({"endpoint": "https://attacker.invalid/v1/chat/completions"}, {"model": "muse-spark-1.3-contributor"}, {"timeout": 31}, {"max_output_tokens": True}, {"ledger_path": "relative.sqlite3"}, {"max_attempts": 21}):
            with self.assertRaises(ValueError):
                MetaWorker(**{**base, **change})

    def test_nonfixture_input_never_reserves_or_dispatches(self):
        calls = []
        worker = self.worker(lambda *args: calls.append(args))
        with self.assertRaises(Rejected):
            worker.execute("one", "room", "product", {**self.intent, "brief": "Private customer text"}, {})
        self.assertEqual(calls, [])
        self.assertEqual(worker.metrics("room")["model_calls"], 0)

    def test_provider_payload_and_fingerprint_share_role_scoped_inputs(self):
        sent = []
        def capture(request, timeout):
            sent.append(json.loads(request.data))
            return response_for(request, timeout)
        worker = self.worker(capture)
        for role, irrelevant, relevant in (
            ("product", {"refund_days": 14}, {"audience": "Members"}),
            ("engineering", {"audience": "Members"}, {"refund_days": 14}),
        ):
            intents = [self.intent, {**self.intent, **irrelevant}, {**self.intent, **relevant}]
            payloads, fingerprints = [], []
            for index, intent in enumerate(intents):
                worker.execute(f"{role}:{index}", "room", role, intent, {})
                payloads.append(sent[-1])
                fingerprints.append(task_input(role, intent, {}, worker.configuration))
            self.assertEqual(payloads[0], payloads[1], "Ignored cache fields must not reach the model")
            self.assertEqual(fingerprints[0], fingerprints[1])
            self.assertNotEqual(payloads[0], payloads[2])
            self.assertNotEqual(fingerprints[0], fingerprints[2])
            inputs = json.loads(payloads[0]["messages"][1]["content"])["inputs"]
            self.assertEqual(set(inputs), {"brief", "audience"} if role == "product" else {"refund_days"})

    def test_structured_request_and_usage_survive_reopen(self):
        requests = []
        def capture(request, timeout):
            requests.append((request, timeout))
            return response_for(request, timeout)
        worker = self.worker(capture)
        output = worker.execute("one", "room", "product", self.intent, {})
        self.assertEqual(output["audience"], "Customers")
        request, timeout = requests[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, ENDPOINT)
        self.assertEqual(body["max_completion_tokens"], 600)
        self.assertFalse(body["store"])
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertEqual(body["messages"][0]["role"], "developer")
        self.assertNotIn("tools", body)
        self.assertEqual(timeout, 20)
        reopened = self.worker(capture)
        self.assertEqual(reopened.metrics("room")["reported_total_tokens"], 140)
        self.assertIsNone(reopened.metrics("room")["actual_billed_usd"])
        with self.assertRaises(Rejected):
            reopened.execute("one", "room", "product", self.intent, {})
        self.assertEqual(len(requests), 1)

    def test_timeout_is_unknown_held_and_never_retried(self):
        calls = []
        def timeout(request, seconds):
            calls.append(1)
            raise TimeoutError("synthetic transport timeout")
        worker = self.worker(timeout, max_attempts=1)
        with self.assertRaises(Rejected):
            worker.execute("one", "room", "product", self.intent, {})
        reopened = self.worker(timeout, max_attempts=1)
        self.assertEqual(reopened.metrics("room")["unknown_usage_requests"], 1)
        self.assertEqual(reopened.metrics("room")["attempt_slots_remaining"], 0)
        for identity in ("one", "two"):
            with self.assertRaises(Rejected):
                reopened.execute(identity, "room", "product", self.intent, {})
        self.assertEqual(len(calls), 1)

    def test_missing_boolean_negative_and_inconsistent_usage_stay_unknown(self):
        for index, usage in enumerate((None, {"prompt_tokens": True, "completion_tokens": 1, "total_tokens": 2}, {"prompt_tokens": -1, "completion_tokens": 1, "total_tokens": 0}, {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 3})):
            def invalid(request, timeout):
                return {**response_for(request, timeout), "usage": usage}
            worker = self.worker(invalid)
            with self.assertRaises(Rejected):
                worker.execute(str(index), "room", "product", self.intent, {})
        self.assertEqual(worker.metrics("room")["unknown_usage_requests"], 4)

    def test_output_overrun_is_recorded_and_halts_next_dispatch(self):
        calls = []
        def overrun(request, timeout):
            calls.append(1)
            return {**response_for(request, timeout), "usage": {"prompt_tokens": 100, "completion_tokens": 601, "total_tokens": 701}}
        worker = self.worker(overrun)
        with self.assertRaises(Rejected):
            worker.execute("one", "room", "product", self.intent, {})
        self.assertEqual(worker.metrics("room")["reported_total_tokens"], 701)
        with self.assertRaises(Rejected):
            worker.execute("two", "room", "product", self.intent, {})
        self.assertEqual(calls, [1])

    def test_malformed_or_incomplete_outputs_fail_after_usage_record(self):
        variants = [
            lambda r: {**r, "model": "unexpected-model"},
            lambda r: {**r, "choices": [{**r["choices"][0], "finish_reason": "length"}]},
            lambda r: {**r, "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "not JSON"}}]},
            lambda r: {**r, "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "{}", "tool_calls": [{}]}}]},
        ]
        for index, variant in enumerate(variants):
            worker = self.worker(lambda request, timeout: variant(response_for(request, timeout)))
            with self.assertRaises(Rejected):
                worker.execute(str(index), "room", "product", self.intent, {})
        self.assertEqual(worker.metrics("room")["model_calls"], 4)
        self.assertEqual(worker.metrics("room")["unknown_usage_requests"], 0)

    def test_atomic_slots_across_independent_ledger_connections(self):
        path = self.root / "atomic.sqlite3"
        def reserve(index):
            ledger = AttemptLedger(path, "synthetic-test-policy", 2)
            try:
                ledger.reserve(str(index), "room")
                return True
            except Rejected:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            accepted = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(accepted), 2)
        self.assertEqual(AttemptLedger(path, "synthetic-test-policy", 2).metrics("room")["unknown_usage_requests"], 2)
        with self.assertRaises(ValueError):
            AttemptLedger(path, "synthetic-test-policy", 3)

    def test_controller_mode_pinning_and_real_dispatch_counters_with_fake_transport(self):
        worker = self.worker()
        controller = Controller(self.root / "meta.sqlite3", worker=worker)
        try:
            with self.assertRaises(Rejected):
                controller.create({"name": "Private", "display_name": "Member", "brief": "Not a public fixture"})
            owner = controller.create({"name": "Synthetic", "display_name": "Member", "brief": SYNTHETIC_BRIEF})
            csrf = controller.session(owner)["csrf"]
            self.assertEqual(controller.snapshot(owner)["room"]["mode"], "meta")
            self.assertEqual(controller.snapshot(owner)["metrics"]["model_calls"], 0)
            controller.mutate(owner, csrf, "run", {"revision": 1})
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                state = controller.snapshot(owner)
                if all(task["state"] == "COMPLETE" for task in state["tasks"]):
                    break
                time.sleep(.01)
            self.assertTrue(all(task["state"] == "COMPLETE" for task in state["tasks"]))
            self.assertEqual(state["metrics"]["model_calls"], 3)
            self.assertEqual(state["metrics"]["reported_total_tokens"], 420)
        finally:
            controller.close()
        with self.assertRaises(ValueError):
            Controller(self.root / "meta.sqlite3")
        with self.assertRaises(ValueError):
            Controller(worker.ledger.path, worker=worker)


if __name__ == "__main__":
    unittest.main()
