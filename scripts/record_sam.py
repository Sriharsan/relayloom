"""Count the goods in every synthetic delivery photo with SAM 3.1 on this machine and keep each real result.

Usage: python scripts/record_sam.py [--world demo|benchmark|both] [--alt] [--only PHOTO_ID ...]
Needs HF_TOKEN in .env with access to facebook/sam3.1, and RELAYLOOM_SAM_PYTHON pointing to a Python with
Ultralytics 8.4 or newer. Weights are downloaded once to RELAYLOOM_MODELS (default D:/relayloom-models).
Results are cached in fixtures/recorded/sam and replayed later only as "recorded". Photos that repeat another
photo of the same delivery are counted once, like the app does. --alt also makes the Investigator's recount with
a second wording of the prompt.
"""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relayloom.ap.app import load_env  # noqa: E402
from relayloom.ap.models import SamCounter  # noqa: E402
from relayloom.ap.receiving import Receiving  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def weights() -> str:
    from huggingface_hub import hf_hub_download
    folder = Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models")) / "facebook_sam3.1"
    return hf_hub_download("facebook/sam3.1", "sam3.1_multiplex.pt", local_dir=folder, token=os.environ["HF_TOKEN"])


def main():
    load_env()
    args = sys.argv[1:]
    world_name = args[args.index("--world") + 1] if "--world" in args else "both"
    only = set(args[args.index("--only") + 1:]) if "--only" in args else set()
    alt = "--alt" in args
    counter = SamCounter(os.environ.get("RELAYLOOM_SAM_PYTHON", "D:/relayloom-models/venv-sam/Scripts/python.exe"),
                         weights(), "SAM 3.1 (sam3.1_multiplex.pt), Ultralytics, CPU, this laptop", live=True)
    for name, file in (("demo", "data.json"), ("benchmark", "benchmark.json")):
        if world_name not in (name, "both"):
            continue
        world = json.loads((FIXTURES / file).read_text(encoding="utf-8"))
        receiving = Receiving(world, counter, FIXTURES)
        for event in world["receiving_events"]:
            if only and not any(p["id"] in only for p in event["photos"]):
                continue
            result = receiving.count_event(event["id"])
            for row in result["photos"]:
                if not row["counted"]:
                    print(f"{row['photo']}: duplicate of {row['duplicate_of']} (similarity {row['similarity']}), not counted", flush=True)
                    continue
                truth = next(p["true_count"] for p in event["photos"] if p["id"] == row["photo"])
                print(f"{row['photo']}: {row['count']} {row['prompt']} ({'correct' if row['count'] == truth else f'expected {truth}'}), "
                      f"{row['seconds']} s", flush=True)
            if alt:
                again = receiving.recount_event(event["id"])
                for row in again["photos"]:
                    print(f"{row['photo']} recount '{row['prompt']}': {row['second']} (first {row['first']})", flush=True)


if __name__ == "__main__":
    main()
