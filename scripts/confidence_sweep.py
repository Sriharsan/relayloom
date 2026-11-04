"""How the SAM confidence setting changes the count, on the builder's test photos and on the rendered benchmark photos.

Usage: python scripts/confidence_sweep.py
Re-counts from the saved mask scores (no model needed). Writes docs/CONFIDENCE.md and site-src/src/data/confidence.json.
"""
import glob
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = (0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7)
slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")  # noqa: E731


def real_rows():
    words = json.loads((ROOT / "fixtures" / "real" / "words.json").read_text(encoding="utf-8"))
    hand = json.loads((ROOT / "docs" / "real_hand_counts.json").read_text(encoding="utf-8"))
    out = []
    for key, meta in words.items():
        pid = f"P{meta['source_index'] + 1:02d}"
        if pid in hand:
            scores = json.loads((ROOT / "fixtures" / "recorded" / "real" / f"{key}__{slug(meta['words'][0])}.json").read_text(encoding="utf-8"))["result"]["scores"]
            out.append((pid, hand[pid]["count"], scores))
    return out


def rendered_rows():
    truth = {}
    for src in ("data.json", "benchmark.json"):
        for event in json.loads((ROOT / "fixtures" / src).read_text(encoding="utf-8"))["receiving_events"]:
            for photo in event["photos"]:
                truth[photo["id"]] = photo["true_count"]
    items = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))["items"]
    ok = {i["prompt"] for i in items.values()} | {i["alt_prompt"] for i in items.values()}
    out = []
    for f in glob.glob(str(ROOT / "fixtures" / "recorded" / "sam" / "*.json")):
        saved = json.loads(Path(f).read_text(encoding="utf-8"))["result"]
        key = os.path.basename(f).split("__")[0]
        if key in truth and saved["prompt"] in ok:
            out.append((key, truth[key], saved["scores"]))
    return out


def sweep(rows):
    table = []
    for thr in THRESHOLDS:
        errors = [sum(1 for s in scores if s >= thr) - hand for _, hand, scores in rows]
        table.append({"threshold": thr, "total_abs_error": sum(abs(e) for e in errors), "exact": sum(1 for e in errors if e == 0),
                      "within_10_percent": sum(1 for e, (_, hand, _) in zip(errors, rows) if abs(e) <= max(1, round(0.1 * hand))), "photos": len(rows)})
    return table


def main():
    real, rendered = sweep(real_rows()), sweep(rendered_rows())
    (ROOT / "site-src" / "src" / "data" / "confidence.json").write_text(json.dumps({"real": real, "rendered": rendered}, indent=1), encoding="utf-8")
    lines = ["# SAM confidence: what the setting does", "",
             "SAM 3.1 returns a score for every mask. Raising the lowest score kept (`--confidence`) removes doubtful masks. The count is recomputed from the saved scores, "
             "so every row is a real model run.", "",
             "## Builder's test photos (8 photos with a hand count, first word)", "", "| Lowest score kept | Total error in items | Exact | Within 10 percent |", "| --- | --- | --- | --- |"]
    lines += [f"| {r['threshold']} | {r['total_abs_error']} | {r['exact']} of {r['photos']} | {r['within_10_percent']} of {r['photos']} |" for r in real]
    lines += ["", "## Rendered benchmark photos (102 runs with a known count)", "", "| Lowest score kept | Total error in items | Exact | Within 10 percent |", "| --- | --- | --- | --- |"]
    lines += [f"| {r['threshold']} | {r['total_abs_error']} | {r['exact']} of {r['photos']} | {r['within_10_percent']} of {r['photos']} |" for r in rendered]
    lines += ["", "Reading it: on real photos 0.4 over-counts (doubtful masks on clutter and far items) and 0.5 to 0.55 is much closer. On the clean rendered photos 0.4 is best. "
              "No single number is best everywhere, so it is a setting. The command defaults to 0.5 because real photos are what it is for. "
              "The value was chosen on 8 photos, so treat it as a starting point and check it on your own goods.", ""]
    (ROOT / "docs" / "CONFIDENCE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(real)); print(json.dumps(rendered))


if __name__ == "__main__":
    main()
