"""Compare SAM 3.1 counts on the builder-provided test photos with hand counts, and write the table for the site and docs.

Usage: python scripts/real_accuracy.py
Reads fixtures/real/words.json, fixtures/recorded/real/*.json and the hand counts in docs/real_hand_counts.json.
Writes site-src/src/data/real.json, site-src/public/img/real/overlay/*.jpg and docs/REAL_GOODS.md.
"""
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
WORDS = json.loads((ROOT / "fixtures" / "real" / "words.json").read_text(encoding="utf-8"))
HAND = json.loads((ROOT / "docs" / "real_hand_counts.json").read_text(encoding="utf-8"))
SAM = ROOT / "fixtures" / "recorded" / "real"
OVERLAYS = ROOT / "site-src" / "public" / "img" / "real" / "overlay"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    OVERLAYS.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, meta in WORDS.items():
        pid = f"P{meta['source_index'] + 1:02d}"
        results = []
        for word in meta["words"]:
            saved = json.loads((SAM / f"{key}__{slug(word)}.json").read_text(encoding="utf-8"))["result"]
            shutil.copy(SAM / saved["overlay"], OVERLAYS / saved["overlay"])
            results.append({"word": word, "count": saved["count"], "seconds": saved["infer_seconds"], "overlay": saved["overlay"]})
        hand = HAND.get(pid)
        counts = [r["count"] for r in results]
        best = min(results, key=lambda r: abs(r["count"] - hand["count"])) if hand else None
        rows.append({"key": key, "pid": pid, "image": f"/img/real/{key}.jpg", "results": results, "agree": counts[0] == counts[1],
                     "hand_count": hand["count"] if hand else None, "hand_by": hand["by"] if hand else None,
                     "first_word_error": (counts[0] - hand["count"]) if hand else None,
                     "best_error": (best["count"] - hand["count"]) if hand else None})
    (ROOT / "site-src" / "src" / "data" / "real.json").write_text(json.dumps({"rows": rows}, indent=1), encoding="utf-8")
    counted = [r for r in rows if r["hand_count"] is not None]
    exact_first = sum(1 for r in counted if r["first_word_error"] == 0)
    within2 = sum(1 for r in counted if abs(r["first_word_error"]) <= max(1, round(0.1 * r["hand_count"])))
    lines = ["# Builder-provided test photos: SAM 3.1 against hand counts", "",
             "Photos are builder-provided test images, a mix of free-licence stock and the builder's own, not a claim about real deliveries. "
             "Each was counted with two words by SAM 3.1 on this laptop's CPU. Hand counts include far items; those marked `assistant` were counted by eye from the picture.", "",
             "| Photo | Word 1 | Word 2 | Words agree | Hand count | Counted by | Error of word 1 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['pid']} | {r['results'][0]['word']}: {r['results'][0]['count']} | {r['results'][1]['word']}: {r['results'][1]['count']} | "
                     f"{'yes' if r['agree'] else 'no'} | {r['hand_count'] if r['hand_count'] is not None else 'no hand count'} | {r['hand_by'] or ''} | "
                     f"{'' if r['first_word_error'] is None else f'{r[chr(102)+chr(105)+chr(114)+chr(115)+chr(116)+chr(95)+chr(119)+chr(111)+chr(114)+chr(100)+chr(95)+chr(101)+chr(114)+chr(114)+chr(111)+chr(114)]:+d}'} |")
    lines += ["", f"Of {len(counted)} photos with a hand count, word 1 was exact on {exact_first} and within 10 percent on {within2}. "
              f"On {sum(1 for r in rows if r['agree'])} of {len(rows)} photos both words gave the same number. "
              "When both words agree on a wrong number the agreement rule cannot catch it; that is why the agent also looks at the numbered overlay and why a person approves a held bill.", ""]
    (ROOT / "docs" / "REAL_GOODS.md").write_text("\n".join(lines), encoding="utf-8")
    print(len(rows), "photos;", len(counted), "with hand counts; exact", exact_first, "within 10 percent", within2)


if __name__ == "__main__":
    main()
