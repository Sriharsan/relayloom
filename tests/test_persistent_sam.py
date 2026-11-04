"""The persistent SAM worker protocol: load once, one JSON line per request, a bad request never stops it."""
from pathlib import Path
import tempfile
import unittest

from relayloom.ap.models import SamCounter

STUB = '''import json, sys
print(json.dumps({"ready": True, "load_seconds": 0.1}), flush=True)
for line in sys.stdin:
    req = json.loads(line)
    if req["prompt"] == "boom":
        print(json.dumps({"error": "ValueError: bad prompt"}), flush=True)
    else:
        Path = __import__("pathlib").Path
        Path(req["overlay"]).write_bytes(b"x")
        print(json.dumps({"count": len(req["prompt"]), "prompt": req["prompt"], "infer_seconds": 0.0}), flush=True)
'''


class PersistentSamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.photo = self.tmp / "p.jpg"
        self.photo.write_bytes(b"photo")
        (self.tmp / "stub.py").write_text(STUB, encoding="utf-8")
        import sys
        self.sam = SamCounter(sys.executable, "w.pt", "stub", live=True, cache=self.tmp / "cache", persistent=True)
        self.sam.worker_script = self.tmp / "stub.py"
        self.addCleanup(self.sam.close)

    def test_one_process_answers_many_requests_and_results_are_saved(self):
        first = self.sam.count(self.photo, "box", "k")
        pid = self.sam._proc.pid
        second = self.sam.count(self.photo, "carton", "k")
        self.assertEqual((first["count"], second["count"]), (3, 6))
        self.assertEqual(self.sam._proc.pid, pid)  # the same process, the model was loaded once
        self.assertTrue((self.tmp / "cache" / "k__box.json").exists())
        again = self.sam.count(self.photo, "box", "k")  # now from the saved result, no request sent
        self.assertTrue(again["recorded"])

    def test_a_bad_request_is_an_error_not_a_dead_worker(self):
        with self.assertRaises(RuntimeError):
            self.sam.count(self.photo, "boom", "k")
        self.assertEqual(self.sam.count(self.photo, "box", "k")["count"], 3)

    def test_a_worker_that_dies_is_restarted_for_the_next_request(self):
        self.sam.count(self.photo, "box", "k")
        old = self.sam._proc.pid
        self.sam._proc.kill()
        self.sam._proc.wait()
        self.assertEqual(self.sam.count(self.photo, "carton", "k")["count"], 6)
        self.assertNotEqual(self.sam._proc.pid, old)


if __name__ == "__main__":
    unittest.main()
