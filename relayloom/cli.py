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
    return SamCounter(python, weights, "SAM 3.1 on this machine", live=live, cache=HOME / "sam-cache", persistent=True)


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


def validate_po(po) -> None:
    if not isinstance(po, dict) or not isinstance(po.get("items"), list) or not po["items"]:
        raise UserError("the purchase order must be a JSON object with an items list")
    for number, line in enumerate(po["items"], start=1):
        for key in ("item_code", "description", "qty", "rate_inr"):
            if not isinstance(line, dict) or line.get(key) in (None, ""):
                raise UserError(f"purchase order line {number} has no {key}")
        if not isinstance(line["qty"], (int, float)) or isinstance(line["qty"], bool) or line["qty"] <= 0:
            raise UserError(f"purchase order line {number} needs a quantity above zero")
        if not isinstance(line["rate_inr"], (int, float)) or isinstance(line["rate_inr"], bool) or line["rate_inr"] < 0:
            raise UserError(f"purchase order line {number} needs a price of zero or more")
    for key in ("po_number", "supplier_id"):
        if not isinstance(po.get(key), str) or not po[key]:
            raise UserError(f"the purchase order has no {key}")
    po.setdefault("tax_rate", 0)


def parse_counts(tokens: list[str], codes: list[str], first: str) -> dict:
    """--counted 46 means the line being counted; --counted CODE=46 CODE2=8 gives each line its own count."""
    given: dict = {}
    for token in tokens:
        code, sep, number = token.partition("=")
        if not sep:
            code, number = first, token
        if code not in codes:
            raise UserError(f"{code} is not on the purchase order (lines: {', '.join(codes)})")
        try:
            value = float(number)
        except ValueError as error:
            raise UserError(f"a count must be a number, not {number!r}") from error
        if value != value or value in (float("inf"), float("-inf")):
            raise UserError("a count must be a finite number")
        value = int(value) if value == int(value) else value  # whole items stay whole; weights and hours may have decimals
        if value < 0:
            raise UserError("a count cannot be negative")
        given[code] = value
    return given


def check(args) -> int:
    from .ap.matcher import match
    from .ap.masking import mask
    from .ap.policy import load_policy
    from .ap.receipts import ReceiptChain, Signer, sha256
    from .ap.schema import Invalid, validate_bill

    quiet = args.json
    policy = load_policy()
    po = load_json(args.po, "purchase order")
    validate_po(po)
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

    codes = [i["item_code"] for i in po["items"]]
    item = next((i for i in po["items"] if i["item_code"] == args.item), None) if args.item else po["items"][0]
    if item is None:
        raise UserError(f"--item {args.item} is not on the purchase order (lines: {', '.join(codes)})")
    given = parse_counts(args.counted, codes, item["item_code"]) if args.counted else {}
    if args.counts_file:
        from_file = load_json(args.counts_file, "counts file")
        if not isinstance(from_file, dict):
            raise UserError("the counts file must be a JSON object like {\"CODE\": 12}")
        given.update(parse_counts([f"{k}={v}" for k, v in from_file.items()], codes, item["item_code"]))
    total, rows, counted_held = 0, [], False
    model, route, input_hash = "none", "given by the person", sha256({"counted": given})
    if item["item_code"] not in given:
        if not args.photos:
            raise UserError("give --photos, or --counted N (or CODE=N for each line) when the goods were counted another way")
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
        given[item["item_code"]] = total
    else:
        total = given[item["item_code"]]
        rows = [{"photo": "(count given with --counted)", "count": total}]
    missing = [c for c in codes if c not in given]
    if missing:
        raise UserError(f"the purchase order has {len(codes)} lines; give a count for each with --counted CODE=N. Missing: {', '.join(missing)}")
    if hasattr(locals().get("sam"), "close"):
        sam.close()
    chain.append(case, "Counter", "count", "counted " + ", ".join(f"{c} {n}" for c, n in given.items()), input_hash=input_hash, model=model, route=route,
                 detail={"photos": rows, "counts": given})

    result = match(po, bill, given, {}, policy.limits)
    needs_approval = bool(result.get("over_limit"))  # the policy lets a person, not the agent, approve a bill over the amount limit
    state = "held" if (not result["matched"] or counted_held or needs_approval) else "clear to enter"
    if needs_approval:
        result["problems"].append(f"total {bill['total_inr']:.2f} is over the owner approval limit of {policy.limits['owner_amount_limit_inr']:g}, so a person approves it")
    chain.append(case, "Matcher", "match", state, input_hash=sha256(result), detail={"problems": result["problems"]})
    receipts = out / "receipts.jsonl"
    if args.json:
        print(json.dumps({"bill_no": bill["bill_no"], "billed": bill["lines"][0]["qty"], "counted": total, "counts": given, "state": state,
                          "problems": result["problems"], "counted_held": counted_held, "receipts": str(receipts),
                          "public_key": chain.signer.public_key}, indent=1))
    else:
        shown = ", ".join(f"{c} {n}" for c, n in given.items())
        billed = ", ".join("{} {:g}".format(l["item_code"], l["qty"]) for l in bill["lines"])
        print()
        print(f"Bill {bill['bill_no']}: billed {billed}; counted {shown}. Result: {state.upper()}")
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
    try:
        receipts = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except ValueError as error:
        raise UserError(f"{path.name} is not a receipt file (a line is not valid JSON: {error})") from error
    if not receipts:
        print("0 receipts: nothing to verify")
        return 1
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
    row("ok" if module_ok("clip") else "todo", "clip (Ultralytics CLIP, used by SAM 3.1 text prompts)", "",
        "" if module_ok("clip") else "python -m pip install git+https://github.com/ultralytics/CLIP.git")
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
    if getattr(args, "report", False):
        home = str(Path.home())
        print()
        print("--- paste this into a bug report (no bills, photos, keys or tokens are included) ---")
        print(f"relayloom {__version__}  python {sys.version.split()[0]}  {sys.platform}")
        for level, what, detail, fix in rows:
            print(f"{level:8} {what}" + (f"  {detail.replace(home, '~')}" if detail and level != 'ok' else ""))
        print("--- end ---")
        print("Report it at https://github.com/Sriharsan/relayloom/issues/new/choose")
    return 0 if core else 1


def update_check(args) -> int:
    """The one command that goes online, and only when asked: is there a newer release on PyPI?"""
    try:
        data = json.loads(urllib.request.urlopen("https://pypi.org/pypi/relayloom/json", timeout=8).read())
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise UserError("no relayloom release was found on PyPI yet") from error
        raise UserError(f"PyPI answered with an error ({error.code})") from error
    except (OSError, ValueError, urllib.error.URLError) as error:
        raise UserError(f"could not reach PyPI ({error}). relayloom never goes online unless you run this command.") from error
    latest = data["info"]["version"]
    def key(v):
        return [int(x) if x.isdigit() else 0 for x in v.split(".")]
    if key(latest) > key(__version__):
        print(f"relayloom {latest} is available (you have {__version__}). Upgrade with: python -m pip install -U relayloom")
    else:
        print(f"relayloom {__version__} is the latest release.")
    return 0


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
    c.add_argument("--counts-file", help="a JSON file of counts, {\"CODE\": N, ...}, for purchase orders with many lines")
    c.add_argument("--counted", nargs="+", metavar="N|CODE=N", help="items already counted instead of photos: N for the line being counted, or CODE=N for each line")
    c.add_argument("--item", help="the purchase order line the photos count (default: the first line)")
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
    d.add_argument("--report", action="store_true", help="print a block to paste into a bug report")
    d.set_defaults(run=doctor)
    u = sub.add_parser("update-check", help="ask PyPI whether a newer release exists (the only command that goes online)")
    u.set_defaults(run=update_check)
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
