"""Video evidence end to end: a dock clip, key frames, SAM 3.1 counts, the full case.

Usage:
    python scripts/video_demo.py --build     make the demo clip from two delivery photos and find the key frames
    python scripts/video_demo.py --count     count the key frames with SAM 3.1 on this machine (a few minutes on a CPU)
    python scripts/video_demo.py             run the case from the saved frames and counts, write site-src/src/data/video.json

The clip is synthetic: two pallet photographs slide into an empty dock. The watcher, the key frames, the SAM 3.1 counts and
the case are real. A camera stream goes through the same reader as a file.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.alerts import AlertHub  # noqa: E402
from relayloom.ap.app import load_env  # noqa: E402
from relayloom.ap.ledger import LocalLedger  # noqa: E402
from relayloom.ap.models import SamCounter  # noqa: E402
from relayloom.ap.pipeline import Network, Workbench  # noqa: E402
from relayloom.ap.policy import load_policy  # noqa: E402
from relayloom.ap.receipts import ReceiptChain, Signer, verify  # noqa: E402
from relayloom.ap.schema import validate_bill  # noqa: E402
from relayloom.ap.video import DockWatcher, make_demo_clip, save_frames  # noqa: E402

F = ROOT / "fixtures"
VIDEO = F / "video"
FRAMES = VIDEO / "frames"
DATA = json.loads((F / "data.json").read_text(encoding="utf-8"))
EVENT_ID, PO, BILL_NO = "REC-V01", "PO-2010", "CAL-1001"


def build():
    VIDEO.mkdir(parents=True, exist_ok=True)
    photos = [cv2.imread(str(F / "photos" / f"REC-H06-P{n}.jpg")) for n in (1, 2)]
    clip = make_demo_clip(VIDEO / "dock-delivery.mp4", photos)
    detected = []
    events = DockWatcher().watch(str(clip), on_detect=detected.append)
    assert len(events) == 1, f"expected one delivery, found {len(events)}"
    for old in FRAMES.glob("*.jpg"):
        old.unlink()
    paths = save_frames(events[0], FRAMES, EVENT_ID)
    capture = cv2.VideoCapture(str(clip))
    meta = {"seconds": round(capture.get(cv2.CAP_PROP_FRAME_COUNT) / capture.get(cv2.CAP_PROP_FPS), 1), "fps": capture.get(cv2.CAP_PROP_FPS),
            "size": [int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))]}
    capture.release()
    event = {"clip": meta, "detection": detected[0], "started_s": events[0]["started_s"], "ended_s": events[0]["ended_s"],
             "median_ms_per_frame": events[0]["median_ms_per_frame"],
             "frames": [{"id": p.stem, "file": f"video/frames/{p.name}", "t": k["t"], "sharpness": k["sharpness"]}
                        for p, k in zip(paths, events[0]["frames"])]}
    (VIDEO / "event.json").write_text(json.dumps(event, indent=1), encoding="utf-8")
    print(f"clip {meta['seconds']} s, delivery detected {detected[0]['detection_lag_s']} s after the first movement, "
          f"{len(paths)} key frames at {[f['t'] for f in event['frames']]} s, {event['median_ms_per_frame']} ms per frame")


def counter(live: bool):
    load_env()
    weights = os.environ.get("RELAYLOOM_SAM_WEIGHTS") or str(Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models")) / "facebook_sam3.1" / "sam3.1_multiplex.pt")
    python = os.environ.get("RELAYLOOM_SAM_PYTHON", "D:/relayloom-models/venv-sam/Scripts/python.exe")
    return SamCounter(python, weights, "SAM 3.1 (sam3.1_multiplex.pt), Ultralytics, CPU, this laptop", live=live)


def count():
    event = json.loads((VIDEO / "event.json").read_text(encoding="utf-8"))
    sam = counter(live=True)
    item = DATA["items"]["CARTON-HD"]
    for frame in event["frames"]:
        for prompt in (item["prompt"], item["alt_prompt"]):
            result = sam.count(F / frame["file"], prompt, frame["id"])
            print(f"{frame['id']} '{prompt}': {result['count']} in {result['infer_seconds']} s", flush=True)


def case():
    event = json.loads((VIDEO / "event.json").read_text(encoding="utf-8"))
    data = copy.deepcopy(DATA)
    data["purchase_orders"].append({"po_number": PO, "supplier_id": "SUP-CALDER", "tax_rate": 0.18,
                                    "items": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0}]})
    source = next(c for c in data["cases"] if c["case"] == "short")
    expected = copy.deepcopy(source["expected_bill"])
    expected.update(bill_no=BILL_NO, po_number=PO, bill_date="2026-11-03")
    record = {"case": "video", "bill_no": BILL_NO, "supplier_id": "SUP-CALDER", "po_number": PO, "bill_pdf": source["bill_pdf"],
              "bill_text": source["bill_text"], "event_ids": [EVENT_ID], "expected_bill": expected, "truth": ""}
    data["cases"].append(record)

    class Reader:
        route = "bench"

        def read_bill(self, masked_text, key=""):
            return {"bill": validate_bill(copy.deepcopy(expected)), "model": "bill record", "route": "bench", "seconds": 0.0, "response_id": "bench-video"}

        def draft_dispute(self, facts, key=""):
            return {"text": f"Bill {facts['bill_no']} on {facts['po_number']}: {facts['problems'][0]} Please send a credit note for the difference.",
                    "model": "template", "route": "bench", "seconds": 0.0, "response_id": "bench-video-d"}

    class Portal:
        def submit(self, case):
            return {"reference": "DSP-VIDEO", "filled_by": "code", "seconds": 0.0}

    hub = AlertHub()
    watcher_log = event["detection"]
    hub.publish("detected", "Delivery detected on the dock camera",
                f"Movement at {watcher_log['detected_at_s']} s of the clip, {watcher_log['detection_lag_s']} s after it began. "
                f"{len(event['frames'])} steady views are being counted.", "dock-camera")
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        policy = load_policy()
        signer = Signer(root / "key")
        chain = ReceiptChain(root / "r.jsonl", signer, policy.hash)
        ledger = LocalLedger(root / "l.sqlite3")
        ledger.seed(data["suppliers"], data["purchase_orders"], data["history_invoices"])
        bench = Workbench(policy, ledger, ledger, chain, Reader(), counter(live=False), Network(ledger), F, data, portal=Portal())
        bench.notify = lambda kind, title, body, case_id, key="", params=None: hub.publish(kind, title, body, case_id, key, params)
        bench.receiving.add_event({"id": EVENT_ID, "po_number": PO, "item_code": "CARTON-HD", "date": "2026-11-03",
                                   "photos": [{"id": f["id"], "file": f["file"]} for f in event["frames"]], "note": "Key frames from a dock video"})
        started = time.perf_counter()
        [done] = bench.run_batch([record])
        seconds = round(time.perf_counter() - started, 2)
        ok, problems = verify(chain.read(), signer.public_key)
        view = done.view()
        ledger.db.close()
    frames = []
    for photo in view["counter"]["events"][0]["photos"]:
        match = next(f for f in event["frames"] if f["id"] == photo["photo"])
        frames.append({**match, "count": photo["count"], "counted": photo["counted"], "seconds": photo.get("seconds"),
                       "overlay": photo.get("overlay", "")})
    out = {"clip": event["clip"], "detection": event["detection"], "median_ms_per_frame": event["median_ms_per_frame"],
           "frames": frames, "total": view["counter"]["total"], "billed": expected["lines"][0]["qty"], "state": view["state"],
           "status": view["status"], "diagnosis": view["diagnosis"], "alerts": hub.items, "receipts_verified": ok,
           "pipeline_seconds": seconds, "problems": problems}
    img = ROOT / "site-src" / "public" / "img"
    img.mkdir(parents=True, exist_ok=True)
    for f in frames:
        shutil.copyfile(F / f["file"], img / f"{f['id']}.jpg")
        if f["overlay"] and (F / "recorded" / "sam" / f["overlay"]).exists():
            shutil.copyfile(F / "recorded" / "sam" / f["overlay"], img / f["overlay"])
    (ROOT / "site-src" / "src" / "data" / "video.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    d = view["diagnosis"] or {}
    print(f"{len(frames)} frames counted {[f['count'] for f in frames]} = {out['total']} of {out['billed']} billed; case {view['state']}; "
          f"cause: {d.get('label')} ({d.get('confidence')}); alerts: {[a['kind'] for a in hub.items]}; receipts verified: {ok}")
    sys.exit(0 if ok and view["state"] in ("held_for_owner", "dispute_sent") else 1)


if __name__ == "__main__":
    flags = sys.argv[1:]
    if "--build" in flags:
        build()
    elif "--count" in flags:
        count()
    else:
        case()
