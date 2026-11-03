"""Run the look agent live on this machine: Muse Glimmer proposes words, calls SAM 3.1, looks at the overlay.

Usage: python scripts/look_live.py PHOTO "bill line text" [--truth N] [--out DIR]
Needs llama-server with Muse Glimmer and its --mmproj on GLIMMER_URL (default http://127.0.0.1:8084/v1). The trace of
every tool call is saved as JSON next to the overlays, so the run can be shown and checked later.
"""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.lookagent import LookAgent  # noqa: E402
from relayloom.ap.models import GlimmerClient, SamCounter  # noqa: E402

MODELS = Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models"))
ROUTE = "Muse Glimmer 30B Q4_K_M with mmproj, llama.cpp CPU, SAM 3.1 CPU, this laptop"


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    photo, line = Path(args[0]), args[1]
    truth = int(args[args.index("--truth") + 1]) if "--truth" in args else None
    out = Path(args[args.index("--out") + 1]) if "--out" in args else ROOT / "fixtures" / "recorded" / "agent"
    out.mkdir(parents=True, exist_ok=True)
    glimmer = GlimmerClient(os.environ.get("GLIMMER_URL", "http://127.0.0.1:8084/v1"), ROUTE, timeout=1800)
    sam = SamCounter(os.environ.get("RELAYLOOM_SAM_PYTHON", str(MODELS / "venv-sam" / "Scripts" / "python.exe")),
                     str(MODELS / "facebook_sam3.1" / "sam3.1_multiplex.pt"), "SAM 3.1 (sam3.1_multiplex.pt), Ultralytics, CPU, this laptop",
                     live=True, cache=out / "sam")
    started = time.strftime("%Y-%m-%d %H:%M %z")
    found = LookAgent(glimmer, sam).look(photo, line, photo.stem)
    record = {"photo": photo.name, "bill_line": line, "hand_count": truth, "recorded_at": started, "route": ROUTE, **found}
    record["first_try_correct"] = None if truth is None or found["first_try_count"] is None else found["first_try_count"] == truth
    record["agent_correct"] = None if truth is None else (found["count"] == truth if found["agreed"] else None)
    (out / f"{photo.stem}.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    for step in found["trace"]:
        print(step["step"], step.get("words", ""), step.get("count", step.get("output", "")), flush=True)
    print(f"count={found['count']} agreed={found['agreed']} held={found['held']} first_try={found['first_try_count']} truth={truth} in {found['seconds']} s")


if __name__ == "__main__":
    main()
