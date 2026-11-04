"""Count the real-goods test photos in fixtures/real/ with SAM 3.1, two words each, and save overlays and results.

Usage: python scripts/real_counts.py   (needs SAM 3.1 on this machine; results go to fixtures/recorded/real/)
"""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.models import SamCounter  # noqa: E402

MODELS = Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models"))


def main():
    words = json.loads((ROOT / "fixtures" / "real" / "words.json").read_text(encoding="utf-8"))
    sam = SamCounter(os.environ.get("RELAYLOOM_SAM_PYTHON", str(MODELS / "venv-sam" / "Scripts" / "python.exe")),
                     str(MODELS / "facebook_sam3.1" / "sam3.1_multiplex.pt"), "SAM 3.1 (sam3.1_multiplex.pt), Ultralytics, CPU, this laptop",
                     live=True, cache=ROOT / "fixtures" / "recorded" / "real")
    for key, meta in words.items():
        for word in meta["words"]:
            result = sam.count(ROOT / "fixtures" / "real" / f"{key}.jpg", word, key)
            print(key, word, result["count"], result.get("infer_seconds"), flush=True)


if __name__ == "__main__":
    main()
