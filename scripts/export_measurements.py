"""Collect the real model measurements the site shows.

Usage: python scripts/export_measurements.py OUT_JSON

SAM 3.1: every recorded run in fixtures/recorded/sam (count, prompt, seconds, overlay image).
Muse Glimmer 30B: the seven bill readings recorded on 31 Oct 2026, read from git history at commit 6597d87^
(their bills belonged to an earlier fixture set; only the timings and schema results are exported).
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SAM = ROOT / "fixtures" / "recorded" / "sam"
DEMO = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
BENCH = json.loads((ROOT / "fixtures" / "benchmark.json").read_text(encoding="utf-8"))
WORLDS = (("demo", DEMO), ("benchmark", BENCH))
TRUE = {p["id"]: p["true_count"] for _, w in WORLDS for e in w["receiving_events"] for p in e["photos"]}
ITEMS = {e["id"]: w["items"][e["item_code"]]["name"] for _, w in WORLDS for e in w["receiving_events"]}
WORLD = {e["id"]: name for name, w in WORLDS for e in w["receiving_events"]}
# The two wordings the system uses per item: the first count and the Investigator's independent recount.
USED = {e["id"]: {w["items"][e["item_code"]]["prompt"], w["items"][e["item_code"]]["alt_prompt"]}
        for _, w in WORLDS for e in w["receiving_events"]}
GLIMMER_COMMIT = "6597d87^"
GLIMMER_FILES = ["read-VEL-2611", "read-PON-0457", "read-NIL-1189", "read-VEL-2614", "read-KAV-0091",
                 "read-PON-0460", "read-NIL-1192"]


def sam_runs():
    runs = []
    for path in sorted(SAM.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        result = record["result"]
        photo = path.stem.split("__")[0]
        runs.append({"photo": photo, "item": ITEMS[photo.rsplit("-", 1)[0]], "prompt": result["prompt"],
                     "count": result["count"], "truth": TRUE[photo], "infer_seconds": result["infer_seconds"],
                     "wall_seconds": result["wall_seconds"], "device": result["device"], "route": result["route"],
                     "overlay": result["overlay"], "recorded_at": record["recorded_at"],
                     "used": result["prompt"] in USED[photo.rsplit("-", 1)[0]],
                     "world": WORLD[photo.rsplit("-", 1)[0]]})
    return runs


def glimmer_runs():
    runs = []
    for number, name in enumerate(GLIMMER_FILES, 1):
        text = subprocess.run(["git", "-C", str(ROOT), "show", f"{GLIMMER_COMMIT}:fixtures/recorded/glimmer/{name}.json"],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout
        record = json.loads(text)
        reply = record["reply"]
        usage = reply.get("usage") or {}
        runs.append({"bill": f"Bill {number}", "seconds": reply["seconds"], "model": reply["model"].split("/")[-1],
                     "route": reply["route"], "prompt_tokens": usage.get("prompt_tokens"),
                     "output_tokens": usage.get("completion_tokens"), "schema_check": record["schema_check"],
                     "recorded_at": record["recorded_at"]})
    return runs


def main():
    out = Path(sys.argv[1])
    sam, glimmer = sam_runs(), glimmer_runs()
    export = {"sam": sam, "glimmer": glimmer, "machine": {
        "os": "Windows 11 Home 10.0.26300", "cpu": "Intel Core Ultra 7 155U, 12 cores, 14 threads",
        "memory": "31.4 GB", "gpu": "Intel integrated graphics, no NVIDIA GPU"}}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(export, indent=1), encoding="utf-8")
    print(f"{len(sam)} SAM 3.1 runs, {len(glimmer)} Muse Glimmer readings -> {out}")


if __name__ == "__main__":
    main()
