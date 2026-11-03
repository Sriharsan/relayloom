"""Video evidence: a delivery is detected at once, steady key frames are kept, quiet docks raise nothing."""
import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from relayloom.ap.receiving import Receiving
from relayloom.ap.video import DockWatcher, make_demo_clip, save_frames

PHOTOS = Path(__file__).resolve().parents[1] / "fixtures" / "photos"


def pallet(seed, size=(120, 160)):
    rng = np.random.default_rng(seed)
    image = rng.integers(40, 220, (*size, 3), dtype=np.uint8)
    return cv2.GaussianBlur(image, (3, 3), 0)


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def clip(self, images, name="dock.avi"):
        return make_demo_clip(self.root / name, images, size=(320, 240), fps=10, hold=2.0, slide=0.6, lead=1.0, tail=4.5, codec="MJPG")

    def test_a_delivery_is_detected_at_once_and_each_distinct_view_is_kept(self):
        detected = []
        events = DockWatcher().watch(str(self.clip([pallet(1), pallet(2)])), on_detect=detected.append)
        self.assertEqual(len(detected), 1)
        self.assertLess(detected[0]["detection_lag_s"], 0.5)  # the alert follows the first movement within half a second
        self.assertGreaterEqual(detected[0]["first_motion_s"], 0.8)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0]["frames"]), 2)
        self.assertLess(events[0]["median_ms_per_frame"], 50)  # cheap enough to keep up with a live camera

    def test_a_quiet_dock_raises_nothing_even_with_sensor_noise(self):
        path = self.root / "quiet.avi"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (320, 240))
        rng = np.random.default_rng(7)
        for _ in range(80):
            noise = rng.integers(-2, 3, (240, 320, 3))
            writer.write(np.clip(72 + noise, 0, 255).astype(np.uint8))
        writer.release()
        detected = []
        self.assertEqual(DockWatcher().watch(str(path), on_detect=detected.append), [])
        self.assertEqual(detected, [])

    def test_two_separate_deliveries_are_two_events(self):
        path = self.root / "two.avi"
        first = self.clip([pallet(3)], "a.avi")
        second = self.clip([pallet(4)], "b.avi")
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (320, 240))
        for source in (first, second):
            capture = cv2.VideoCapture(str(source))
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                writer.write(frame)
            capture.release()
        writer.release()
        self.assertEqual(len(DockWatcher().watch(str(path))), 2)

    def test_key_frames_become_a_receiving_event_that_is_counted_and_deduplicated(self):
        events = DockWatcher().watch(str(self.clip([pallet(5), pallet(6)])))
        paths = save_frames(events[0], self.root / "frames", "REC-T01")
        self.assertEqual([p.name for p in paths], ["REC-T01-F1.jpg", "REC-T01-F2.jpg"])
        world = {"receiving_events": [], "items": {"BOX": {"prompt": "box", "alt_prompt": "package"}}}

        class Counter:
            def count(self, photo, prompt, key):
                return {"count": 10 if key.endswith("F1") else 7, "route": "fake", "infer_seconds": 0.0}

        receiving = Receiving(world, Counter(), self.root)
        receiving.add_event({"id": "REC-T01", "po_number": "PO-T", "item_code": "BOX", "date": "2026-11-03",
                             "photos": [{"id": p.stem, "file": str(p)} for p in paths] + [{"id": "REC-T01-F3", "file": str(paths[0])}]})
        counted = receiving.count_event("REC-T01")
        self.assertEqual(counted["total"], 17)
        self.assertEqual(counted["duplicate_photos"], 1)  # a repeated view is counted once
        self.assertEqual(receiving.received_for_po("PO-T")["total"], 17)

    def test_a_source_that_cannot_be_opened_is_refused(self):
        with self.assertRaises(ValueError):
            DockWatcher().watch(str(self.root / "missing.avi"))


if __name__ == "__main__":
    unittest.main()
