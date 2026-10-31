"""Count the goods in each synthetic delivery photo with SAM 3.1 on this machine and save the real result.

Usage: python scripts/record_sam.py [BILL_NO ...] [--sam3]
Needs HF_TOKEN in .env with access granted to facebook/sam3.1 (or facebook/sam3 with --sam3), and
RELAYLOOM_SAM_PYTHON pointing to a Python with Ultralytics 8.4 or newer. Weights are downloaded once
to RELAYLOOM_MODELS (default D:/relayloom-models). Outputs are replayed only as "recorded".
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relayloom.ap.app import load_env  # noqa: E402
from relayloom.ap.models import SamCounter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "recorded" / "sam"


def weights(sam3: bool) -> str:
    from huggingface_hub import hf_hub_download
    repo, name = ("facebook/sam3", "sam3.pt") if sam3 else ("facebook/sam3.1", "sam3.1_multiplex.pt")
    folder = Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models")) / repo.replace("/", "_")
    return hf_hub_download(repo, name, local_dir=folder, token=os.environ["HF_TOKEN"])


def main():
    load_env()
    sam3 = "--sam3" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = weights(sam3)
    model = "SAM 3" if sam3 else "SAM 3.1"
    route = os.environ.get("SAM_ROUTE", f"{model} ({Path(path).name}), Ultralytics, CPU, this laptop")
    counter = SamCounter(os.environ.get("RELAYLOOM_SAM_PYTHON", "D:/relayloom-models/venv-sam/Scripts/python.exe"),
                         path, OUT, route)
    data = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for case in data["cases"]:
        if args and case["bill_no"] not in args:
            continue
        photo = ROOT / "fixtures" / case["photo"]
        result = counter.count(photo, case["count_prompt"], case["bill_no"])
        result["model"] = model
        result["weights_sha256_16"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
        record = {"recorded_at": time.strftime("%Y-%m-%d %H:%M %z"), "machine": platform.processor() or platform.machine(),
                  "photo_sha256": hashlib.sha256(photo.read_bytes()).hexdigest(),
                  "delivered_in_photo": case["delivered_in_photo"], "result": result}
        (OUT / f"{case['bill_no']}.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
        verdict = "correct" if result["count"] == case["delivered_in_photo"] else f"expected {case['delivered_in_photo']}"
        print(f"{case['bill_no']}: {result['count']} {case['count_prompt']} ({verdict}), "
              f"inference {result['infer_seconds']} s, load {result['load_seconds']} s, wall {result['wall_seconds']} s", flush=True)


if __name__ == "__main__":
    main()
