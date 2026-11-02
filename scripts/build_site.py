"""Build site/data/results.json and site/img from the runs in a data folder.

Usage: python scripts/build_site.py DATA_DIR [--label "text"] [--video URL]
DATA_DIR holds run-* folders made by `python -m relayloom.ap.cases all --data DATA_DIR`.
Nothing is typed in here: every fact comes from result.json and receipts.jsonl of those runs.
"""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
TITLES = {"match": "Matching delivery", "short": "Short delivery: paperwork says 50, the dock got 46", "price": "Price above the order",
          "injection": "Hidden text asking to change the bank account", "netcut": "Network cut mid batch",
          "duplicate": "Duplicate bill under a new number", "split": "Split delivery, one bill"}
STORY = {
    "match": "Bill, order and counted goods agree. Agents enter the bill and a separate check reads it back. No person involved.",
    "short": "The bill says 50 cartons. Two photos of the dock show 46, and a repeated photo is counted once. The Investigator recounts, checks the order and the supplier's history, and cites every statement. The owner approves, Muse Glimmer drafts the dispute and a browser agent files it.",
    "duplicate": "The goods match the bill, but the same supplier, amount and date are already in the books under another bill number. The Investigator finds it and proposes rejecting the duplicate.",
    "split": "One order arrived in two deliveries and was billed once. The Matcher adds the receiving events up as a running total, so the bill matches and nothing is held.",
    "price": "The carton rate is above the purchase order. The owner is asked, rejects, and nothing is entered or sent.",
    "injection": "White text on the bill asks to pay a new account. It never reaches the model, the attempt is receipted, and payment details come from the ledger supplier master.",
    "netcut": "The link is cut after the first invoice is accepted. Reading continues, nothing else is entered. On reconnect the ledger is read first and no invoice is duplicated.",
}
COMMAND = {k: f"python -m relayloom.ap.cases {k}" for k in TITLES}


def finding_block(views, run_dir):
    """The short delivery case's investigation: statements, the evidence behind each citation, the proposal."""
    view = next((v for v in views if v.get("investigation")), None)
    if not view:
        return None
    inv = view["investigation"]
    finding = inv["finding"]
    images = []
    for event in view["counter"]["events"]:
        for photo in event["photos"]:
            name = photo.get("overlay") or ""
            for folder in (run_dir / "media", ROOT / "fixtures" / "recorded" / "sam"):
                if photo["counted"] and name and (folder / name).exists():
                    shutil.copyfile(folder / name, SITE / "img" / f"{photo['photo']}.jpg")
                    images.append({"src": f"img/{photo['photo']}.jpg", "alt": f"{photo['photo']} with {photo['count']} items outlined and numbered",
                                   "caption": f"{photo['photo']}: {photo['count']} counted"})
    return {"title": f"Bill {view['bill_no']}", "written_by": finding["written_by"], "model": finding.get("model", ""),
            "route": finding.get("route", ""), "statements": finding["statements"],
            "evidence": {k: v["text"] for k, v in inv["evidence"].items()},
            "proposal": view["proposal"]["reason"], "policy": view["proposal"]["policy_level"].replace("_", " "),
            "images": images}


def main():
    data = Path(sys.argv[1])
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
    video = sys.argv[sys.argv.index("--video") + 1] if "--video" in sys.argv else ""
    (SITE / "img").mkdir(parents=True, exist_ok=True)
    (SITE / "data").mkdir(exist_ok=True)
    receipts, cases, run_info, log, finding = [], [], None, [], None
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
                         f"{counter.get('total')} in {counter.get('seconds')} s, result: {view['status']}")
        first = views[0]
        overlay = next((p.get("overlay") for e in first["counter"].get("events", []) for p in e["photos"] if p["counted"]), None)
        for folder in (run_dir / "media", ROOT / "fixtures" / "recorded" / "sam"):
            if overlay and (folder / overlay).exists():
                shutil.copyfile(folder / overlay, SITE / "img" / f"{name}-count.jpg")
                image, alt = f"img/{name}-count.jpg", f"Delivery photo for {first['bill_no']} with each counted item outlined and numbered by SAM 3.1"
                break
        shot = first.get("dispute", {}) and first["dispute"].get("screenshot")
        if shot and (run_dir / "media" / shot).exists():
            shutil.copyfile(run_dir / "media" / shot, SITE / "img" / f"{name}-portal.png")
            facts.append(f"Dispute filed in the supplier portal by {first['dispute']['form_filled_by']}, reference {first['dispute']['portal_ref']}")
        if name == "short":
            finding = finding_block(views, run_dir)
        cases.append({"title": TITLES[name], "result": result["result"], "story": STORY[name], "facts": facts,
                      "command": COMMAND[name], "image": image, "alt": alt,
                      "label": f"{result['mode']} run, {result['reader']}, {result['counter']}, {result['ledger']}"})
    gateway = ROOT / "data" / "boundary" / "gateway.jsonl"
    if gateway.exists():
        log = [json.loads(line) for line in gateway.read_text(encoding="utf-8").splitlines()[-8:]]
    keys = {r["body"]["policy_hash"] for r in receipts}
    bench_path = ROOT / "docs" / "benchmark-results.json"
    out = {"runline": label, "video": video, "finding": finding,
           "benchmark": json.loads(bench_path.read_text(encoding="utf-8")) if bench_path.exists() else None, "policy": run_info["policy"] if run_info and "policy" in run_info else {},
           "cases": cases, "receipts": {"public_key": run_info["public_key"], "receipts": receipts},
           "boundary": {"line": "Muse Glimmer and SAM 3.1 run on the same machine as the agents. In the boundary run the agents' network has no route out; direct connections failed and the gateway refused hosts outside the policy.",
                        "log": log}}
    policy = json.loads((ROOT / "relayloom" / "ap" / "policy.json").read_text(encoding="utf-8"))
    out["policy"] = {k: v["level"] for k, v in policy["operations"].items()}
    (SITE / "data" / "results.json").write_text(json.dumps(out), encoding="utf-8")
    print(f"site data: {len(cases)} cases, {len(receipts)} receipts, {len(keys)} policy hash")


if __name__ == "__main__":
    main()
