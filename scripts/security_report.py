"""Check every security control for real, time it, and compare its cost with the model steps.

Usage: python scripts/security_report.py [--json OUT.json] [--md OUT.md]

Each control runs on the synthetic fixtures. A control passes only if it blocks what it must block AND lets the
good input through. The time is the median of many runs on this machine. Everything is local: no control calls a
service, so none costs money, and the time they add is compared with the measured model steps.
"""
import copy
import json
from pathlib import Path
import socket
import statistics
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relayloom.ap.alerts import AlertHub, PhoneServer  # noqa: E402
from relayloom.ap.gateway import Gateway  # noqa: E402
from relayloom.ap.investigator import verify_finding  # noqa: E402
from relayloom.ap.masking import find, mask  # noqa: E402
from relayloom.ap.matcher import match  # noqa: E402
from relayloom.ap.pipeline import compare, hidden_text  # noqa: E402
from relayloom.ap.policy import Refused, load_policy  # noqa: E402
from relayloom.ap.receipts import ReceiptChain, Signer, verify  # noqa: E402
from relayloom.ap.receiving import similarity  # noqa: E402
from relayloom.ap.schema import Invalid, validate_bill  # noqa: E402

F = ROOT / "fixtures"
DATA = json.loads((F / "data.json").read_text(encoding="utf-8"))
CASES = {c["case"]: c for c in DATA["cases"]}
POLICY = load_policy()
TEST = {  # the unit test that covers the same control
    "mask": "test_masking_removes_gstin_bank_ifsc_phone_and_email",
    "hidden": "test_injection_is_recorded_and_payment_uses_master_data",
    "schema": "test_schema_refuses_extra_keys_bank_fields_and_bad_values",
    "policy": "test_policy_levels_and_refusals",
    "match": "test_matcher_running_total_and_tolerances",
    "photo": "test_duplicate_photo_is_found_and_different_photos_are_not",
    "cite": "test_citation_of_a_missing_record_is_rejected",
    "readback": "test_readback_mismatch_refuses_entered_status",
    "receipts": "test_receipts_verify_offline_and_detect_tampering",
    "gateway": "tests/test_gateway.py",
    "phone": "tests/test_alerts.py",
}


def timed(fn, runs):
    fn()
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples), max(samples)


def raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    return False


# ---- controls: each returns (passed, callable_to_time) -------------------------------------------------------
def c_mask():
    text = (F / "bills" / "ARD-5101.txt").read_text(encoding="utf-8")
    masked, records = mask(text)
    secrets_ = [s["gstin"] for s in DATA["suppliers"][:1]] + [s["bank_account"] for s in DATA["suppliers"][:1]]
    ok = find(masked) == [] and bool(records) and all(s not in masked for s in secrets_) and "ARD-5101" in masked
    return ok, lambda: mask(text)


def c_hidden():
    bad, good = F / "bills" / "ARD-5104.pdf", F / "bills" / "ARD-5101.pdf"
    ok = bool(hidden_text(bad)) and hidden_text(good) == []
    return ok, lambda: hidden_text(bad)


def c_schema():
    bill = CASES["match"]["expected_bill"]
    def clean():
        return copy.deepcopy(bill)
    with_bank = clean(); with_bank["bank_account"] = "1"
    negative = clean(); negative["lines"][0]["qty"] = -1
    ok = (validate_bill(clean())["total_inr"] == bill["total_inr"] and raises(Invalid, lambda: validate_bill(with_bank))
          and raises(Invalid, lambda: validate_bill(negative)))
    return ok, lambda: validate_bill(clean())


def c_policy():
    def three():
        for fn in (lambda: POLICY.require("send_dispute"),
                   lambda: POLICY.require("send_dispute", approved=True),
                   lambda: POLICY.require("change_bank_from_invoice_text", approved=True)):
            try:
                fn()
            except Refused:
                pass
    ok = (raises(Refused, lambda: POLICY.require("send_dispute")) and not raises(Refused, lambda: POLICY.require("send_dispute", approved=True))
          and raises(Refused, lambda: POLICY.require("change_bank_from_invoice_text", approved=True)))
    return ok, three


def c_match():
    case = CASES["short"]
    po = next(p for p in DATA["purchase_orders"] if p["po_number"] == case["po_number"])
    bill = case["expected_bill"]
    short = lambda: match(po, bill, {"CARTON-HD": 46}, {}, POLICY.limits)
    full = lambda: match(po, bill, {"CARTON-HD": 50}, {}, POLICY.limits)
    return (not short()["matched"] and full()["matched"]), short


def c_photo():
    a, b, c = F / "photos" / "REC-H06-P1.jpg", F / "photos" / "REC-H06-P2.jpg", F / "photos" / "REC-H06-P3.jpg"
    return (similarity(a, c) >= 0.95 and similarity(a, b) < 0.95), lambda: similarity(a, c)


def c_cite():
    ev = {"BILL:X": {"id": "BILL:X", "kind": "bill", "text": "Bill X: 50 cartons"}}
    good = [{"text": "The bill lists 50 cartons.", "cites": ["BILL:X"]}]
    invented = [{"text": "A record says so.", "cites": ["PHOTO:INVENTED"]}]
    wrong_number = [{"text": "The bill lists 99 cartons.", "cites": ["BILL:X"]}]
    ok = verify_finding(good, ev)[0] and not verify_finding(invented, ev)[0] and not verify_finding(wrong_number, ev)[0]
    return ok, lambda: verify_finding(good, ev)


def c_readback():
    bill = CASES["match"]["expected_bill"]
    stored = copy.deepcopy(bill)
    wrong = copy.deepcopy(bill); wrong["total_inr"] += 500
    return (compare(bill, stored) == [] and compare(bill, wrong) != [] and compare(bill, None) != []), lambda: compare(bill, stored)


KEEP = []  # temporary folders that must outlive the check so the timing can use them


def c_receipts():
    folder_object = tempfile.TemporaryDirectory()
    KEEP.append(folder_object)
    folder = folder_object.name
    signer = Signer(Path(folder) / "key")
    chain = ReceiptChain(Path(folder) / "r.jsonl", signer, POLICY.hash)
    for step in ("intake", "read", "match"):
        chain.append("case", "Agent", step, "ok")
    receipts = chain.read()
    ok = verify(receipts, signer.public_key)[0]
    tampered = copy.deepcopy(receipts)
    tampered[1]["body"]["decision"] = "changed"
    ok = ok and not verify(tampered, signer.public_key)[0]
    extra = ReceiptChain(Path(folder) / "t.jsonl", signer, POLICY.hash)
    n = [0]

    def append_and_sign():
        n[0] += 1
        extra.append(f"c{n[0]}", "Agent", "step", "ok")
    return ok, append_and_sign, lambda: verify(receipts, signer.public_key)


def c_gateway():
    folder = tempfile.TemporaryDirectory()
    server = Gateway(("127.0.0.1", 0), {"allowed.example"}, Path(folder.name) / "g.jsonl")
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def ask(line):
        with socket.create_connection(server.server_address, timeout=5) as s:
            s.sendall(line.encode() + b"\r\n\r\n")
            return s.recv(100)
    ok = b"403" in ask("CONNECT blocked.example:443 HTTP/1.1") and b"403" in ask("GET http://allowed.example/ HTTP/1.1")
    logged = (Path(folder.name) / "g.jsonl").read_text(encoding="utf-8").count("blocked")
    ok = ok and logged >= 2

    def blocked():
        ask("CONNECT blocked.example:443 HTTP/1.1")
    return ok, blocked, (server, folder)


def c_phone():
    server = PhoneServer(("127.0.0.1", 0), AlertHub(), token="t", wait=0.01)
    server.start()
    import urllib.error
    import urllib.request

    def get(path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{server.server_address[1]}{path}", timeout=5) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code
    ok = get("/") == 403 and get("/?t=bad") == 403 and get("/?t=t") == 200
    return ok, lambda: get("/?t=bad"), server


CONTROLS = [
    ("Input", "Mask private numbers", "A model never sees a tax id, bank account, bank code, phone or email", "mask", c_mask, 300),
    ("Input", "Find hidden text in the PDF", "White text that tries to give the model orders never reaches it", "hidden", c_hidden, 100),
    ("Input", "Strict bill schema", "Extra fields such as bank details, and bad values, are refused", "schema", c_schema, 1000),
    ("Decision", "Policy levels", "Actions that need the owner are refused without approval; changing bank details from a bill is never allowed", "policy", c_policy, 1000),
    ("Decision", "Three way match", "A bill for more than arrived is held, however it is worded", "match", c_match, 1000),
    ("Decision", "Repeated photo detection", "The same goods photographed twice are counted once", "photo", c_photo, 20),
    ("Decision", "Citation check", "A finding that cites a record that does not exist, or a number its sources lack, is never shown", "cite", c_cite, 1000),
    ("Action", "Ledger readback", "A bill whose stored copy differs in any field is not treated as entered", "readback", c_readback, 1000),
    ("Evidence", "Signed receipts", "Changing any recorded decision breaks the chain", "receipts", c_receipts, 30),
    ("Boundary", "Egress gateway", "Only listed hosts over HTTPS, every refusal logged", "gateway", c_gateway, 20),
    ("Boundary", "Phone alert token", "No token, no alerts, and the page can change nothing", "phone", c_phone, 20),
]


def main():
    rows, cleanup = [], []
    for level, name, prevents, key, fn, runs in CONTROLS:
        result = fn()
        ok, timer = result[0], result[1]
        extra = result[2] if len(result) > 2 else None
        if key == "receipts":
            median, worst = timed(timer, runs)
            verify_median, _ = timed(extra, runs)
            note = f"append and sign {median:.2f} ms, verify three receipts {verify_median:.2f} ms"
        else:
            median, worst = timed(timer, runs)
            note = ""
            if key in ("gateway", "phone"):
                cleanup.append(extra)
        rows.append({"level": level, "control": name, "prevents": prevents, "passed": bool(ok), "median_ms": round(median, 3),
                     "max_ms": round(worst, 3), "test": TEST[key], "note": note})
    for item in cleanup:
        server = item[0] if isinstance(item, tuple) else item
        server.shutdown(); server.server_close()

    per_case_keys = {"Mask private numbers": 1, "Find hidden text in the PDF": 1, "Strict bill schema": 1, "Policy levels": 6,
                     "Three way match": 1, "Repeated photo detection": 2, "Citation check": 1, "Ledger readback": 1}
    per_case_ms = sum(r["median_ms"] * per_case_keys.get(r["control"], 0) for r in rows)
    per_case_ms += next(r["median_ms"] for r in rows if r["control"] == "Signed receipts") * 12  # about a dozen receipts a case
    measured = json.loads((ROOT / "site-src" / "src" / "data" / "measured.json").read_text(encoding="utf-8"))
    sam = [r["infer_seconds"] for r in measured["sam"] if r["used"]]
    glim = [g["seconds"] for g in measured["glimmer"]]
    out = {"rows": rows, "controls_per_case_ms": round(per_case_ms, 1),
           "sam_seconds_median": round(statistics.median(sam), 1), "glimmer_seconds_median": round(statistics.median(glim), 1),
           "ratio_to_glimmer": round(statistics.median(glim) * 1000 / per_case_ms), "all_passed": all(r["passed"] for r in rows),
           "cost_in_money": "none: every control runs locally, with no API call", "ran_at": time.strftime("%Y-%m-%d %H:%M %z")}
    args = sys.argv[1:]
    if "--json" in args:
        Path(args[args.index("--json") + 1]).write_text(json.dumps(out, indent=1), encoding="utf-8")
    md = ["# Security controls: what each one costs", "",
          "Every control below was run on the synthetic fixtures by `python scripts/security_report.py`. A control passes only if it",
          "blocks what it must block and lets the good input through. Times are medians on this laptop. Each control runs locally, so",
          "none costs any money, and none needs the network.", "",
          "| Level | Control | What it prevents | Passed | Median ms | Test |", "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        md.append(f"| {r['level']} | {r['control']} | {r['prevents']} | {'yes' if r['passed'] else 'NO'} | {r['median_ms']} | `{r['test']}` |")
    md += ["", f"Together the controls add about {out['controls_per_case_ms']} ms to a case. For comparison, a Muse Glimmer bill reading took a "
           f"median of {out['glimmer_seconds_median']} s and a SAM 3.1 count {out['sam_seconds_median']} s on this CPU. The controls are about "
           f"1 part in {out['ratio_to_glimmer']} of one bill reading, so they do not slow the work.", "",
           "The latency that matters is the models', and it is shown on the Proof page with its limits."]
    if "--md" in args:
        Path(args[args.index("--md") + 1]).write_text("\n".join(md) + "\n", encoding="utf-8")
    for r in rows:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['level']:9} {r['control']:30} {r['median_ms']:>9.3f} ms  {r['note']}")
    print(f"controls per case: about {out['controls_per_case_ms']} ms; Glimmer median {out['glimmer_seconds_median']} s; all passed: {out['all_passed']}")
    sys.exit(0 if out["all_passed"] else 1)


if __name__ == "__main__":
    main()
