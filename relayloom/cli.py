"""The relayloom command line.

relayloom check    match one bill against a purchase order and the photos of the goods, hold it if the goods are short
relayloom verify   check a receipt file offline: signatures, hashes and chain order
relayloom doctor   say what is ready on this machine and what is missing
relayloom serve    start the accounts payable demo app on this machine
relayloom models   pull the open weight models and start Muse Glimmer locally

Everything runs on this machine. Nothing is sent anywhere, and the receipts are signed with a key kept in your own
folder. Exit codes for check: 0 clear to enter, 3 held, 2 could not run.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

from . import __version__

HOME = Path(os.environ.get("RELAYLOOM_HOME", Path.home() / ".relayloom"))
MODELS = Path(os.environ.get("RELAYLOOM_MODELS", HOME / "models"))
GLIMMER_REPO, GLIMMER_FILES = "meta-models/Muse-Glimmer-30B-GGUF", ("Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf", "mmproj-Muse-Glimmer-30B-Q4_K_M.gguf")
SAM_REPO, SAM_FILE = "facebook/sam3.1", "sam3.1_multiplex.pt"
PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


class UserError(Exception):
    """Something the person can fix: a missing file, a bad purchase order, a model that is not running."""


def say(message: str, quiet: bool = False):
    if not quiet:
        print(message, flush=True)


def expand_photos(items: list[str]) -> list[Path]:
    """Files, or folders of photos, in a stable order."""
    found: list[Path] = []
    for item in items:
        path = Path(item)
        if path.is_dir():
            found.extend(sorted(p for p in path.iterdir() if p.suffix.lower() in PHOTO_SUFFIXES))
        else:
            found.append(path)
    missing = [str(p) for p in found if not p.exists()]
    if missing or not found:
        raise SystemExit("photos not found: " + (", ".join(missing) or "none given"))
    return found


def read_bill_text(path: Path) -> str:
    if not path.exists():
        raise UserError(f"bill not found: {path}")
    if path.suffix.lower() == ".pdf":
        import fitz  # PyMuPDF
        with fitz.open(path) as document:
            return "\n".join(page.get_text() for page in document)
    return path.read_text(encoding="utf-8")


def load_json(path: str, what: str) -> dict:
    target = Path(path)
    if not target.exists():
        raise UserError(f"{what} not found: {target}")
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except ValueError as error:
        raise UserError(f"{what} is not valid JSON: {error}") from error


def build_sam(live: bool = True):
    from .ap.models import SamCounter
    python = os.environ.get("RELAYLOOM_SAM_PYTHON", sys.executable)
    weights = os.environ.get("RELAYLOOM_SAM_WEIGHTS", str(MODELS / SAM_FILE))
    if live and not Path(weights).exists():
        raise UserError(f"SAM 3.1 weights not found at {weights}. Run: relayloom models pull   (or use --counted N to skip counting)")
    return SamCounter(python, weights, "SAM 3.1 on this machine", live=live, cache=HOME / "sam-cache")


def glimmer_url() -> str:
    return os.environ.get("GLIMMER_URL", "http://127.0.0.1:8082/v1")


def build_glimmer():
    from .ap.models import GlimmerClient
    return GlimmerClient(glimmer_url(), "Muse Glimmer on this machine")


def glimmer_is_up() -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        return opener.open(glimmer_url().rsplit("/v1", 1)[0] + "/health", timeout=2).status == 200
    except (OSError, ValueError, urllib.error.URLError):
        return False


def check(args) -> int:
    from .ap.matcher import match
    from .ap.masking import mask
    from .ap.policy import load_policy
    from .ap.receipts import ReceiptChain, Signer, sha256
    from .ap.schema import Invalid, validate_bill

    quiet = args.json
    policy = load_policy()
    po = load_json(args.po, "purchase order")
    if not po.get("items"):
        raise UserError("the purchase order needs an items list")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    case = args.case or Path(args.bill or args.bill_json).stem
    chain = ReceiptChain(out / "receipts.jsonl", Signer(HOME / "signing.key"), policy.hash)
    (out / "public_key.txt").write_text(chain.signer.public_key, encoding="utf-8")

    if args.bill_json:
        try:
            bill = validate_bill(load_json(args.bill_json, "bill"))
        except Invalid as error:
            raise UserError(f"the bill does not match the bill schema: {error}") from error
        chain.append(case, "Reader", "read", "given as structured data", input_hash=sha256(bill), detail={"bill": bill})
    else:
        masked, records = mask(read_bill_text(Path(args.bill)))
        if not glimmer_is_up():
            raise UserError(f"Muse Glimmer is not running at {glimmer_url()}. Start it with: relayloom models serve")
        say(f"Reading the bill with Muse Glimmer ({len(records)} private numbers masked first)...", quiet)
        read = build_glimmer().read_bill(masked)
        bill = read["bill"]
        chain.append(case, "Reader", "read", "extracted", input_hash=sha256(masked.encode()), model=read["model"],
                     route=read["route"], response_id=read["response_id"], detail={"bill": bill, "seconds": read["seconds"]})

    item = po["items"][0]
    total, rows, counted_held = 0, [], False
    if args.counted is not None:
        total = args.counted
        rows = [{"photo": "(count given with --counted)", "count": total}]
        input_hash = sha256({"counted": total})
        route, model = "given by the person", "none"
    else:
        if not args.photos:
            raise UserError("give --photos, or --counted N when the goods were counted another way")
        photos = expand_photos(args.photos)
        sam = build_sam()
        model, route, input_hash = "SAM 3.1", "this machine", sha256([p.name for p in photos])
        if args.agent:
            from .ap.lookagent import LookAgent
            if not glimmer_is_up():
                raise UserError(f"the agent needs Muse Glimmer at {glimmer_url()}. Start it with: relayloom models serve")
            agent = LookAgent(build_glimmer(), sam)
            for photo in photos:
                say(f"The agent is looking at {photo.name}...", quiet)
                found = agent.look(photo, item["description"], photo.stem, seed_words=args.words or ())
                rows.append({"photo": photo.name, "count": found["count"], "held": found["held"], "confirmed_by": found.get("confirmed_by", ""),
                             "trace": found["trace"]})
                if found["held"]:
                    say(f"  no two counts agree for {photo.name}; a person should count it", quiet)
                total += found["count"] or 0
            counted_held = any(r.get("held") for r in rows)
        else:
            words = args.words or [item["description"].split(",")[0]]
            for photo in photos:
                say(f"Counting {photo.name} with SAM 3.1 for '{words[0]}'...", quiet)
                result = sam.count(photo, words[0], photo.stem)
                rows.append({"photo": photo.name, "count": result["count"], "words": words[0], "seconds": result.get("infer_seconds")})
                total += result["count"]
    chain.append(case, "Counter", "count", f"counted {total}", input_hash=input_hash, model=model, route=route,
                 detail={"photos": rows, "total": total})

    result = match(po, bill, {item["item_code"]: total}, {}, policy.limits)
    state = "held" if (not result["matched"] or counted_held) else "clear to enter"
    chain.append(case, "Matcher", "match", state, input_hash=sha256(result), detail={"problems": result["problems"]})
    receipts = out / "receipts.jsonl"
    if args.json:
        print(json.dumps({"bill_no": bill["bill_no"], "billed": bill["lines"][0]["qty"], "counted": total, "state": state,
                          "problems": result["problems"], "counted_held": counted_held, "receipts": str(receipts),
                          "public_key": chain.signer.public_key}, indent=1))
    else:
        print(f"\nBill {bill['bill_no']}: billed {bill['lines'][0]['qty']:g}, counted {total}. Result: {state.upper()}")
        for problem in result["problems"]:
            print("  -", problem)
        if counted_held:
            print("  - a photo could not be counted with two agreeing results")
        print(f"Signed receipts: {receipts}   Verify: relayloom verify {receipts}")
    return 0 if state == "clear to enter" else 3


def verify_command(args) -> int:
    from .ap.receipts import verify
    path = Path(args.receipts)
    if not path.exists():
        raise UserError(f"receipt file not found: {path}")
    receipts = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    key_file = Path(args.key_file) if args.key_file else path.with_name("public_key.txt")
    if not args.key and not key_file.exists():
        raise UserError(f"no public key: pass --key, or keep public_key.txt next to {path.name}")
    key = args.key or key_file.read_text(encoding="utf-8").strip()
    ok, problems = verify(receipts, key)
    print(f"{len(receipts)} receipts: " + ("chain verified" if ok else "BROKEN"))
    for problem in problems:
        print("  -", problem)
    return 0 if ok else 1


def module_ok(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def doctor(args) -> int:
    """What is ready, what is missing, and the one command that fixes each. Makes no network calls beyond 127.0.0.1."""
    rows = []

    def row(level: str, what: str, detail: str = "", fix: str = ""):
        rows.append((level, what, detail, fix))

    row("ok" if sys.version_info >= (3, 11) else "missing", f"Python {sys.version.split()[0]}", "needs 3.11 or newer")
    for module, label in (("cryptography", "signed receipts"), ("fitz", "reading PDF bills"), ("cv2", "photo checks"), ("numpy", "photo checks")):
        row("ok" if module_ok(module) else "missing", f"{module} ({label})", "", "" if module_ok(module) else "python -m pip install relayloom")
    weights = Path(os.environ.get("RELAYLOOM_SAM_WEIGHTS", MODELS / SAM_FILE))
    row("ok" if weights.exists() else "todo", "SAM 3.1 weights", str(weights), "" if weights.exists() else "relayloom models pull")
    for name in GLIMMER_FILES:
        have = (MODELS / name).exists()
        row("ok" if have else "todo", f"Muse Glimmer file {name}", str(MODELS / name), "" if have else "relayloom models pull")
    row("ok" if module_ok("ultralytics") else "todo", "ultralytics (runs SAM 3.1)", "", "" if module_ok("ultralytics") else "python -m pip install 'relayloom[models]'")
    binary = shutil.which("llama-server") or os.environ.get("RELAYLOOM_LLAMA", "")
    row("ok" if binary else "todo", "llama-server (llama.cpp)", binary or "not on PATH", "" if binary else "install llama.cpp, or set RELAYLOOM_LLAMA")
    up = glimmer_is_up()
    row("ok" if up else "todo", f"Muse Glimmer running at {glimmer_url()}", "", "" if up else "relayloom models serve")
    row("ok", "Signing key folder", str(HOME))
    marks = {"ok": "ok     ", "todo": "to do  ", "missing": "MISSING"}
    for level, what, detail, fix in rows:
        print(f"{marks[level]} {what}" + (f"  ({detail})" if detail and level != "ok" else "") + (f"  ->  {fix}" if fix else ""))
    ready = all(level == "ok" for level, *_ in rows)
    core = all(level == "ok" for level, what, *_ in rows if what.startswith(("Python", "cryptography", "fitz", "cv2", "numpy")))
    print("\n" + ("Everything is ready for relayloom check --agent." if ready else
                  "Core is ready: relayloom verify and relayloom check --counted work now." if core else "Install the missing core pieces first."))
    return 0 if core else 1


def serve(args) -> int:
    from .ap.app import FIXTURES, main as app_main
    if not (Path(FIXTURES) / "data.json").exists():
        raise UserError("relayloom serve runs the demo app, which needs the repository's demo data. "
                        "Clone https://github.com/Sriharsan/relayloom and run it from there, or use relayloom check on your own files.")
    sys.argv = ["relayloom serve"] + args.rest
    app_main()
    return 0


def models_pull(args) -> int:
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        raise UserError("set HF_TOKEN to your own Hugging Face read token first. SAM 3.1 needs the access request on huggingface.co/facebook/sam3.1.")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as error:
        raise UserError("install the model extras first: python -m pip install 'relayloom[models]'") from error
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
        raise UserError("llama-server (llama.cpp) is not on PATH. Install llama.cpp, or set RELAYLOOM_LLAMA to its path.")
    for name in GLIMMER_FILES:
        if not (MODELS / name).exists():
            raise UserError(f"{MODELS / name} is missing. Run: relayloom models pull")
    command = [binary, "-m", str(MODELS / GLIMMER_FILES[0]), "--mmproj", str(MODELS / GLIMMER_FILES[1]), "--host", "127.0.0.1",
               "--port", str(args.port), "--jinja", "-c", "8192", "-np", "1", "--reasoning-budget", "1024",
               "--chat-template-kwargs", '{"reasoning_strength":"low"}']
    print("Starting Muse Glimmer on 127.0.0.1 only. Press Ctrl+C to stop.", flush=True)
    return subprocess.call(command)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="relayloom", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    top.add_argument("--version", action="version", version=f"relayloom {__version__}")
    top.add_argument("--debug", action="store_true", help="show the full traceback when something fails")
    sub = top.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check", help="match a bill with a purchase order and photos of the goods")
    source = c.add_mutually_exclusive_group(required=True)
    source.add_argument("--bill", help="the bill as a PDF or text file (read by Muse Glimmer)")
    source.add_argument("--bill-json", help="the bill already as structured JSON")
    c.add_argument("--po", required=True, help="purchase order JSON")
    c.add_argument("--photos", nargs="+", help="photos, or folders of photos, of the delivery")
    c.add_argument("--counted", type=int, help="the number of items already counted, instead of photos")
    c.add_argument("--words", nargs="*", help="words for SAM to look for (the agent proposes them when omitted)")
    c.add_argument("--agent", action="store_true", help="let Muse Glimmer choose the words and look at its own counts")
    c.add_argument("--case", help="case name for the receipts")
    c.add_argument("--out", default="relayloom-out", help="folder for the signed receipts")
    c.add_argument("--json", action="store_true", help="print the result as JSON for scripts")
    c.set_defaults(run=check)
    v = sub.add_parser("verify", help="verify a receipt file offline")
    v.add_argument("receipts")
    v.add_argument("--key", help="public key (base64)")
    v.add_argument("--key-file", help="file with the public key; default public_key.txt next to the receipts")
    v.set_defaults(run=verify_command)
    d = sub.add_parser("doctor", help="say what is ready on this machine and what is missing")
    d.set_defaults(run=doctor)
    s = sub.add_parser("serve", help="start the demo app on this machine (extra arguments go to the app)")
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
    try:
        return args.run(args)
    except UserError as error:
        print(f"relayloom: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("relayloom: stopped", file=sys.stderr)
        return 130
    except Exception as error:  # a short message for people, the traceback only with --debug
        if args.debug:
            raise
        print(f"relayloom: {type(error).__name__}: {error}  (run with --debug for the full traceback)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
