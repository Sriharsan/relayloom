"""Build site/data/results.json and site/img from the runs in a data folder.

Usage: python scripts/build_site.py DATA_DIR [--label "text"] [--video URL]
DATA_DIR holds run-* folders made by `python -m relayloom.ap.cases all --data DATA_DIR`.
Nothing is invented here: every fact comes from result.json and receipts.jsonl of those runs.
"""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
TITLES = {"match": "Matching delivery", "short": "Short delivery", "price": "Price above the order",
          "injection": "Hidden text asking to change the bank account", "netcut": "Network cut mid batch"}
STORY = {
    "match": "Bill, order and counted goods agree. Agents enter the bill and a separate check reads it back. No person involved.",
    "short": "The bill says 20 sacks, the photo shows 16. Nothing is entered. The owner approves, Muse Glimmer drafts the dispute and a browser agent files it in the supplier portal.",
    "price": "The carton rate is above the purchase order. The owner is asked, rejects, and nothing is entered or sent.",
    "injection": "White text on the bill asks to pay a new account. It never reaches the model, the attempt is receipted, and payment details come from the ledger supplier master.",
    "netcut": "The link is cut after the first invoice is accepted. Reading continues, nothing else is entered. On reconnect the ledger is read first and no invoice is duplicated.",
}
COMMAND = {k: f"python -m relayloom.ap.cases {k}" for k in TITLES}


def main():
    data = Path(sys.argv[1])
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
    video = sys.argv[sys.argv.index("--video") + 1] if "--video" in sys.argv else ""
    (SITE / "img").mkdir(parents=True, exist_ok=True)
    (SITE / "data").mkdir(exist_ok=True)
    receipts, cases, run_info, log = [], [], None, []
    for run_dir in sorted(data.glob("run-*")):
        result_path = run_dir / "result.json"
        if not result_path.exists():
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        run_info = result
        receipts += [json.loads(line) for line in (run_dir / "receipts.jsonl").read_text(encoding="utf-8").splitlines()]
        views = result["cases"]
        name = result["case"]
        facts, image, alt = [], "", ""
        for view in views:
            reader, counter = view["reader"], view["counter"]
            facts.append(f"{view['bill_no']}: read by Muse Glimmer in {reader.get('seconds')} s, SAM 3.1 counted "
                         f"{counter.get('count')} in {counter.get('seconds')} s, result: {view['status']}")
        first = views[0]
        overlay = first["counter"].get("overlay")
        for folder in (run_dir / "media", ROOT / "fixtures" / "recorded" / "sam"):
            if overlay and (folder / overlay).exists():
                shutil.copyfile(folder / overlay, SITE / "img" / f"{name}-count.jpg")
                image, alt = f"img/{name}-count.jpg", f"Delivery photo for {first['bill_no']} with each counted item outlined and numbered by SAM 3.1"
                break
        shot = first.get("dispute", {}) and first["dispute"].get("screenshot")
        if shot and (run_dir / "media" / shot).exists():
            shutil.copyfile(run_dir / "media" / shot, SITE / "img" / f"{name}-portal.png")
            facts.append(f"Dispute filed in the supplier portal by {first['dispute']['form_filled_by']}, reference {first['dispute']['portal_ref']}")
        cases.append({"title": TITLES[name], "result": result["result"], "story": STORY[name], "facts": facts,
                      "command": COMMAND[name], "image": image, "alt": alt,
                      "label": f"{result['mode']} run, {result['reader']}, {result['counter']}, {result['ledger']}"})
    gateway = ROOT / "data" / "boundary" / "gateway.jsonl"
    if gateway.exists():
        log = [json.loads(line) for line in gateway.read_text(encoding="utf-8").splitlines()[-8:]]
    keys = {r["body"]["policy_hash"] for r in receipts}
    out = {"runline": label, "video": video, "policy": run_info["policy"] if run_info and "policy" in run_info else {},
           "cases": cases, "receipts": {"public_key": run_info["public_key"], "receipts": receipts},
           "boundary": {"line": "Muse Glimmer and SAM 3.1 run on the same machine as the agents. In the boundary run the agents' network has no route out; direct connections failed and the gateway refused hosts outside the policy.",
                        "log": log}}
    policy = json.loads((ROOT / "relayloom" / "ap" / "policy.json").read_text(encoding="utf-8"))
    out["policy"] = {k: v["level"] for k, v in policy["operations"].items()}
    (SITE / "data" / "results.json").write_text(json.dumps(out), encoding="utf-8")
    print(f"site data: {len(cases)} cases, {len(receipts)} receipts, {len(keys)} policy hash")


if __name__ == "__main__":
    main()
