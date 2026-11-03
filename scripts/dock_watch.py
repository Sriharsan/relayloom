"""Watch a dock camera or a video file, and alert a phone the moment a delivery starts.

Usage:
    python scripts/dock_watch.py clip.mp4                 a video file
    python scripts/dock_watch.py 0                        the first camera on this computer
    python scripts/dock_watch.py rtsp://camera/stream     a network camera stream
Options:
    --phone         also serve the alerts to a phone on the same Wi-Fi (read only, token link, no internet)
    --count ITEM    count the key frames with SAM 3.1 on this machine, for example --count CARTON-HD, and alert the total

The delivery alert comes within a fraction of a second of the first movement. Counting is the slow step on a CPU, so it
follows as a second alert. Key frames are saved in data/dock/.
"""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.alerts import AlertHub, PhoneServer, announce  # noqa: E402
from relayloom.ap.video import DockWatcher, save_frames  # noqa: E402


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0].startswith("--"):
        print(__doc__)
        sys.exit(2)
    source = int(args[0]) if args[0].isdigit() else args[0]
    hub = AlertHub()
    if "--phone" in args:
        phone = PhoneServer(("0.0.0.0", 8801), hub)
        phone.start()
        announce(phone)
    item = args[args.index("--count") + 1] if "--count" in args else ""
    folder = ROOT / "data" / "dock" / time.strftime("watch-%Y%m%d-%H%M%S")

    def detected(info):
        message = f"Movement at {info['detected_at_s']} s, {info['detection_lag_s']} s after it began."
        hub.publish("detected", "Delivery detected on the dock", message, "dock")
        print("ALERT  delivery detected.", message, flush=True)

    def finished(event):
        paths = save_frames(event, folder, "DOCK")
        message = f"{len(paths)} steady views saved from {event['started_s']} s to {event['ended_s']} s."
        hub.publish("delivery", "Delivery complete", message, "dock")
        print("ALERT  delivery complete.", message, "Frames:", folder, flush=True)
        if item:
            from relayloom.ap.app import load_env
            from relayloom.ap.models import SamCounter
            load_env()
            data = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
            prompt = data["items"][item]["prompt"]
            models = Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models"))
            sam = SamCounter(os.environ.get("RELAYLOOM_SAM_PYTHON", str(models / "venv-sam" / "Scripts" / "python.exe")),
                             str(models / "facebook_sam3.1" / "sam3.1_multiplex.pt"), "SAM 3.1 on this laptop", live=True, cache=folder / "sam")
            total = 0
            for path in paths:
                total += sam.count(path, prompt, path.stem)["count"]
            hub.publish("counted", f"Counted {total} {prompt}s on the dock", "Match it against the bill before paying.", "dock")
            print(f"ALERT  counted {total} ({prompt}) across {len(paths)} views.", flush=True)

    watcher = DockWatcher()
    try:
        watcher.watch(source, on_detect=detected, on_event=finished)
    except KeyboardInterrupt:
        pass
    print("Finished watching.")


if __name__ == "__main__":
    main()
