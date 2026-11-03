"""The relayloom command line.

relayloom check   match one bill against a purchase order and the photos of the goods, hold it if the goods are short
relayloom verify  check a receipt file offline: signatures, hashes and chain order
relayloom serve   start the accounts payable app on this machine
relayloom models  pull the open weight models and start Muse Glimmer locally

Everything runs on this machine. Nothing is sent anywhere, and the receipts are signed with a key kept in your own
folder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HOME = Path(os.environ.get("RELAYLOOM_HOME", Path.home() / ".relayloom"))
MODELS = Path(os.environ.get("RELAYLOOM_MODELS", HOME / "models"))
GLIMMER_REPO, GLIMMER_FILES = "meta-models/Muse-Glimmer-30B-GGUF", ("Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf", "mmproj-Muse-Glimmer-30B-Q4_K_M.gguf")
SAM_REPO, SAM_FILE = "facebook/sam3.1", "sam3.1_multiplex.pt"
PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def expand_photos(items: list[str]) -> list[Path]:
    """Files, or folders of photos, in a stable order."""
    found: list[Path] = []
    for item in items:
        path = Path(item)
        found.extend(sorted(p for p in path.iterdir() if p.suffix.lower() in PHOTO_SUFFIXES) if path.is_dir() else [path])
    missing = [str(p) for p in found if not p.exists()]
    if missing or not found:
        raise SystemExit("photos not found: " + (", ".join(missing) or "none given"))
    return found


def read_bill_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        import fitz  # PyMuPDF
        with fitz.open(path) as document:
            return "\n".join(page.get_text() for page in document)
    return path.read_text(encoding="utf-8")


def build_sam(live: bool = True):
    from .ap.models import SamCounter
    python = os.environ.get("RELAYLOOM_SAM_PYTHON", sys.executable)
    weights = os.environ.get("RELAYLOOM_SAM_WEIGHTS", str(MODELS / SAM_FILE))
    return SamCounter(python, weights, "SAM 3.1 on this machine", live=live, cache=HOME / "sam-cache")


def build_glimmer():
    from .ap.models import GlimmerClient
    return GlimmerClient(os.environ.get("GLIMMER_URL", "http://127.0.0.1:8082/v1"), "Muse Glimmer on this machine")


def check(args) -> int:
    from .ap.matcher import match
    from .ap.masking import mask
    from .ap.policy import load_policy
    from .ap.receipts import ReceiptChain, Signer, sha256
    from .ap.schema import validate_bill

    policy = load_policy()
    po = json.loads(Path(args.po).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    case = args.case or Path(args.bill or args.bill_json).stem
    chain = ReceiptChain(out / "receipts.jsonl", Signer(HOME / "signing.key"), policy.hash)
    (out / "public_key.txt").write_text(chain.signer.public_key, encoding="utf-8")

    if args.bill_json:
        bill = validate_bill(json.loads(Path(args.bill_json).read_text(encoding="utf-8")))
        chain.append(case, "Reader", "read", "given as structured data", input_hash=sha256(bill), detail={"bill": bill})
    else:
        masked, records = mask(read_bill_text(Path(args.bill)))
        print(f"Reading the bill with Muse Glimmer ({len(records)} private numbers masked first)...", flush=True)
        read = build_glimmer().read_bill(masked)
        bill = read["bill"]
        chain.append(case, "Reader", "read", "extracted", input_hash=sha256(masked.encode()), model=read["model"],
                     route=read["route"], response_id=read["response_id"], detail={"bill": bill, "seconds": read["seconds"]})

    photos = expand_photos(args.photos)
    item = po["items"][0]
    sam = build_sam()
    total, rows = 0, []
    if args.agent:
        from .ap.lookagent import LookAgent
        agent = LookAgent(build_glimmer(), sam)
        for photo in photos:
            print(f"The agent is looking at {photo.name}...", flush=True)
            found = agent.look(photo, item["description"], photo.stem, seed_words=args.words or ())
            rows.append({"photo": photo.name, "count": found["count"], "held": found["held"], "trace": found["trace"]})
            if found["held"]:
                print(f"  no two counts agree for {photo.name}; a person should count it", flush=True)
            total += found["count"] or 0
    else:
        words = args.words or [item["description"].split(",")[0]]
        for photo in photos:
            print(f"Counting {photo.name} with SAM 3.1 for '{words[0]}'...", flush=True)
            result = sam.count(photo, words[0], photo.stem)
            rows.append({"photo": photo.name, "count": result["count"], "words": words[0], "seconds": result.get("infer_seconds")})
            total += result["count"]
    counted_held = any(r.get("held") for r in rows)
    chain.append(case, "Counter", "count", f"counted {total}", input_hash=sha256([p.name for p in photos]),
                 model="SAM 3.1", route="this machine", detail={"photos": rows, "total": total})

    result = match(po, bill, {item["item_code"]: total}, {}, policy.limits)
    state = "held" if (not result["matched"] or counted_held) else "clear to enter"
    chain.append(case, "Matcher", "match", state, input_hash=sha256(result), detail={"problems": result["problems"]})
    print(f"\nBill {bill['bill_no']}: billed {bill['lines'][0]['qty']:g}, counted {total}. Result: {state.upper()}")
    for problem in result["problems"]:
        print("  -", problem)
    if counted_held:
        print("  - a photo could not be counted with two agreeing results")
    print(f"Signed receipts: {out / 'receipts.jsonl'}   Verify: relayloom verify {out / 'receipts.jsonl'}")
    return 0 if state == "clear to enter" else 3


def verify_command(args) -> int:
    from .ap.receipts import verify
    path = Path(args.receipts)
    receipts = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    key_file = Path(args.key_file) if args.key_file else path.with_name("public_key.txt")
    key = args.key or key_file.read_text(encoding="utf-8").strip()
    ok, problems = verify(receipts, key)
    print(f"{len(receipts)} receipts: " + ("chain verified" if ok else "BROKEN"))
    for problem in problems:
        print("  -", problem)
    return 0 if ok else 1


def serve(args) -> int:
    from .ap.app import main as app_main
    sys.argv = ["relayloom serve"] + args.rest
    app_main()
    return 0


def models_pull(args) -> int:
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        print("Set HF_TOKEN to your own Hugging Face read token first. SAM 3.1 needs the access request on huggingface.co/facebook/sam3.1.")
        return 2
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Install the model extras first: python -m pip install 'relayloom[models]'")
        return 2
    MODELS.mkdir(parents=True, exist_ok=True)
    wanted = [(SAM_REPO, SAM_FILE)] + ([] if args.sam_only else [(GLIMMER_REPO, f) for f in GLIMMER_FILES])
    for repo, name in wanted:
        print(f"Downloading {repo}/{name} (large files, one time)...", flush=True)
        hf_hub_download(repo, name, local_dir=MODELS, token=token)
    print(f"Models are in {MODELS}. Offline from here: no network needed to run the checks.")
    return 0


def models_serve(args) -> int:
    binary = shutil.which("llama-server") or os.environ.get("RELAYLOOM_LLAMA", "")
    if not binary:
        print("llama-server (llama.cpp) is not on PATH. Install llama.cpp and try again, or set RELAYLOOM_LLAMA to its path.")
        return 2
    command = [binary, "-m", str(MODELS / GLIMMER_FILES[0]), "--mmproj", str(MODELS / GLIMMER_FILES[1]), "--host", "127.0.0.1",
               "--port", str(args.port), "--jinja", "-c", "8192", "-np", "1", "--reasoning-budget", "1024",
               "--chat-template-kwargs", '{"reasoning_strength":"low"}']
    print("Starting Muse Glimmer on 127.0.0.1 only. Press Ctrl+C to stop.", flush=True)
    return subprocess.call(command)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="relayloom", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = top.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check", help="match a bill with a purchase order and photos of the goods")
    source = c.add_mutually_exclusive_group(required=True)
    source.add_argument("--bill", help="the bill as a PDF or text file (read by Muse Glimmer)")
    source.add_argument("--bill-json", help="the bill already as structured JSON")
    c.add_argument("--po", required=True, help="purchase order JSON")
    c.add_argument("--photos", nargs="+", required=True, help="photos, or folders of photos, of the delivery")
    c.add_argument("--words", nargs="*", help="words for SAM to look for (the agent proposes them when omitted)")
    c.add_argument("--agent", action="store_true", help="let Muse Glimmer choose the words and look at its own counts")
    c.add_argument("--case", help="case name for the receipts")
    c.add_argument("--out", default="relayloom-out", help="folder for the signed receipts")
    c.set_defaults(run=check)
    v = sub.add_parser("verify", help="verify a receipt file offline")
    v.add_argument("receipts")
    v.add_argument("--key", help="public key (base64)")
    v.add_argument("--key-file", help="file with the public key; default public_key.txt next to the receipts")
    v.set_defaults(run=verify_command)
    s = sub.add_parser("serve", help="start the app on this machine (extra arguments go to the app)")
    s.add_argument("rest", nargs=argparse.REMAINDER)
    s.set_defaults(run=serve)
    m = sub.add_parser("models", help="pull or serve the open weight models")
    msub = m.add_subparsers(dest="models_command", required=True)
    pull = msub.add_parser("pull", help="download SAM 3.1 and Muse Glimmer with your own HF_TOKEN")
    pull.add_argument("--sam-only", action="store_true")
    pull.set_defaults(run=models_pull)
    ms = msub.add_parser("serve", help="start Muse Glimmer with llama.cpp on 127.0.0.1")
    ms.add_argument("--port", type=int, default=8082)
    ms.set_defaults(run=models_serve)
    return top


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
