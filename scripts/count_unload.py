"""Count items as they cross a line while goods are carried or unloaded, from a video.

Usage: python scripts/count_unload.py VIDEO PROMPT [--line 0.5] [--axis x|y] [--direction increasing|decreasing|either]
                                      [--every N] [--max-frames M] [--out DIR] [--truth N]
SAM 3.1 tracks every item through the video and keeps its id; the count is the number of ids that cross the line once.
On a CPU use --every to track key frames (and say so); on a GPU leave it at 1. Saves the tracks and the count as JSON.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.crossing import count_crossings  # noqa: E402

MODELS = Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models"))


def option(args, name, default):
    return args[args.index(name) + 1] if name in args else default


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    video, prompt = Path(args[0]), args[1]
    every, limit = int(option(args, "--every", 1)), int(option(args, "--max-frames", 0))
    line, axis, direction = float(option(args, "--line", 0.5)), option(args, "--axis", "x"), option(args, "--direction", "increasing")
    out = Path(option(args, "--out", ROOT / "fixtures" / "recorded" / "tracking"))
    truth = option(args, "--truth", None)
    python = os.environ.get("RELAYLOOM_SAM_PYTHON", str(MODELS / "venv-sam" / "Scripts" / "python.exe"))
    weights = os.environ.get("RELAYLOOM_SAM_WEIGHTS", str(MODELS / "facebook_sam3.1" / "sam3.1_multiplex.pt"))
    worker = ROOT / "relayloom" / "ap" / "track_worker.py"
    command = [python, "-I", str(worker), weights, str(video), prompt, "--every", str(every)] + (["--max-frames", str(limit)] if limit else [])
    started = time.strftime("%Y-%m-%d %H:%M %z")
    done = subprocess.run(command, capture_output=True, text=True, env={**os.environ, "YOLO_OFFLINE": "1"})
    if done.returncode != 0:
        print(done.stderr[-800:])
        sys.exit(1)
    tracked = json.loads(done.stdout.strip().splitlines()[-1])
    found = count_crossings({k: [tuple(p) for p in v] for k, v in tracked["tracks"].items()}, line, axis, direction, margin=0.02)
    record = {"video": video.name, "prompt": prompt, "line": line, "axis": axis, "direction": direction, "recorded_at": started,
              "device": tracked["device"], "every": every, "tracked_seconds": tracked["seconds"], "frames_tracked": tracked["frames"],
              "fps": tracked["fps"], "count": found["count"], "ids": found["ids"], "tracks_seen": found["tracks"],
              "hand_count": int(truth) if truth else None, "rows": found["rows"], "tracks": tracked["tracks"]}
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{video.stem}.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    note = "key frames, CPU" if every > 1 or tracked["device"] == "cpu" else "every frame"
    print(f"counted {found['count']} crossing the line from {found['tracks']} tracks ({note}) in {tracked['seconds']} s; hand count {truth}")


if __name__ == "__main__":
    main()
