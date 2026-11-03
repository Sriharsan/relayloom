"""Run Relayloom with the network physically off, and write a dated report.

Usage (from the repository folder, in a normal terminal):

    python scripts/offline_check.py

It waits until you turn Wi-Fi off (and unplug any cable), proves there is no network, then runs:
  1. one live Muse Glimmer 30B bill reading on this machine,
  2. one live SAM 3.1 count of a delivery photo on this machine,
  3. all seven cases with signed receipts, verified offline.
It writes docs/OFFLINE_RUN.md. When it says "Done", turn Wi-Fi back on.

Test flags (they write no offline claim): --allow-online runs even with the network on, --skip-models skips steps 1 and 2.
"""
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ALLOW_ONLINE = "--allow-online" in sys.argv
SKIP_MODELS = "--skip-models" in sys.argv
MODELS = Path(os.environ.get("RELAYLOOM_MODELS", "D:/relayloom-models"))
LLAMA = Path(os.environ.get("RELAYLOOM_LLAMA", MODELS / "llama-cpu" / "llama-server.exe"))
GLIMMER = Path(os.environ.get("RELAYLOOM_GLIMMER", MODELS / "glimmer" / "Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf"))
SAM_PYTHON = os.environ.get("RELAYLOOM_SAM_PYTHON", str(MODELS / "venv-sam" / "Scripts" / "python.exe"))
SAM_WEIGHTS = Path(os.environ.get("RELAYLOOM_SAM_WEIGHTS", MODELS / "facebook_sam3.1" / "sam3.1_multiplex.pt"))
PORT = 8083
report = {"started": time.strftime("%Y-%m-%d %H:%M %z"), "steps": [], "passed": False}


def say(message):
    print(message, flush=True)


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "result": "PASS" if ok else "FAIL", "detail": detail})
    say(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    return ok


def network_errors():
    """Try to reach the internet three ways. Returns the error for each. All three must fail."""
    out = {}
    for label, target in (("1.1.1.1:443", ("1.1.1.1", 443)), ("8.8.8.8:53", ("8.8.8.8", 53))):
        try:
            socket.create_connection(target, timeout=4).close()
            out[label] = "connected"
        except OSError as error:
            out[label] = f"{type(error).__name__}: {error}"[:90]
    try:
        socket.gethostbyname("example.com")
        out["dns example.com"] = "resolved"
    except OSError as error:
        out["dns example.com"] = f"{type(error).__name__}: {error}"[:90]
    return out


def wait_for_offline():
    say("Turn Wi-Fi off now and unplug any network cable. Waiting for the network to go away (up to 10 minutes).")
    deadline = time.time() + 600
    while time.time() < deadline:
        errors = network_errors()
        if all(v not in ("connected", "resolved") for v in errors.values()):
            return errors
        time.sleep(5)
    return network_errors()


def live_glimmer():
    from relayloom.ap.masking import mask
    from relayloom.ap.models import GlimmerClient
    from relayloom.ap.schema import validate_bill
    data = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
    case = next(c for c in data["cases"] if c["case"] == "match")
    text, _ = mask((ROOT / "fixtures" / case["bill_text"]).read_text(encoding="utf-8"))
    log = MODELS / "llama-offline.log"
    cmd = [str(LLAMA), "-m", str(GLIMMER), "--host", "127.0.0.1", "--port", str(PORT), "--jinja", "-c", "8192", "-np", "1",
           "-t", "10", "--no-repack", "--reasoning-budget", "1024", "--chat-template-kwargs", '{"reasoning_strength":"low"}']
    say("Starting Muse Glimmer on this machine. Loading takes about a minute, reading a bill several minutes.")
    server = subprocess.Popen(cmd, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    try:
        import urllib.request
        for _ in range(60):
            try:
                if urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3).status == 200:
                    break
            except OSError:
                time.sleep(5)
        else:
            return step("live Muse Glimmer bill reading", False, "the model server did not start")
        reader = GlimmerClient(f"http://127.0.0.1:{PORT}/v1", "Muse Glimmer 30B Q4_K_M, llama.cpp, this laptop, network off")
        result = reader.read_bill(text, key=case["bill_no"])
        bill = validate_bill(result["bill"])
        expected = case["expected_bill"]
        same = bill["bill_no"] == expected["bill_no"] and abs(bill["total_inr"] - expected["total_inr"]) < 0.01
        return step("live Muse Glimmer bill reading", same, f"{case['bill_no']} read in {result['seconds']} s, valid schema, total {bill['total_inr']}")
    except Exception as error:
        return step("live Muse Glimmer bill reading", False, f"{type(error).__name__}: {str(error)[:150]}")
    finally:
        server.terminate()


def live_sam():
    from relayloom.ap.models import SamCounter
    try:
        with tempfile.TemporaryDirectory() as cache:
            counter = SamCounter(SAM_PYTHON, str(SAM_WEIGHTS), "SAM 3.1 on this laptop, network off", live=True, cache=Path(cache))
            started = time.perf_counter()
            result = counter.count(ROOT / "fixtures" / "photos" / "REC-H05-P1.jpg", "can", "REC-H05-P1")
            seconds = round(time.perf_counter() - started, 1)
        return step("live SAM 3.1 count", result["count"] == 24, f"counted {result['count']} of 24 cans in {seconds} s")
    except Exception as error:
        return step("live SAM 3.1 count", False, f"{type(error).__name__}: {str(error)[:150]}")


def cases():
    with tempfile.TemporaryDirectory() as data:
        done = subprocess.run([sys.executable, "-m", "relayloom.ap.cases", "all", "--data", data], capture_output=True, text=True,
                              cwd=ROOT, env={**os.environ, "PYTHONWARNINGS": "ignore"})
    lines = [l for l in done.stdout.splitlines() if l.split(":")[0] in ("match", "short", "price", "injection", "netcut", "duplicate", "split")
             and ("PASS in" in l or "FAIL in" in l)]
    summary = ", ".join(l.split(". Receipts")[0] for l in lines)
    return step("seven cases with signed receipts verified offline", done.returncode == 0 and len(lines) == 7, summary)


def main():
    say(f"Relayloom offline check on {platform.node()}, {platform.system()} {platform.release()}")
    errors = network_errors()
    if all(v not in ("connected", "resolved") for v in errors.values()):
        pass
    elif ALLOW_ONLINE:
        say("The network is ON. Test mode: this report makes no offline claim.")
    else:
        errors = wait_for_offline()
    offline = all(v not in ("connected", "resolved") for v in errors.values())
    report["network"] = errors
    if not step("the network is really off", offline, "; ".join(f"{k}: {v}" for k, v in errors.items())) and not ALLOW_ONLINE:
        say("The network is still on, so nothing was run. Turn Wi-Fi off and unplug cables, then start again.")
        sys.exit(2)
    if not SKIP_MODELS:
        live_glimmer()
        live_sam()
    cases()
    report["passed"] = all(s["result"] == "PASS" for s in report["steps"])
    report["finished"] = time.strftime("%Y-%m-%d %H:%M %z")
    title = "Tested fully disconnected" if (offline and not SKIP_MODELS) else "TEST MODE, no offline claim"
    out = ROOT / "docs" / ("OFFLINE_RUN.md" if (offline and not ALLOW_ONLINE and not SKIP_MODELS) else "OFFLINE_RUN_TEST.md")
    md = [f"# {title}", "", f"Started {report['started']}, finished {report['finished']}. Machine: {platform.node()}, "
          f"{platform.system()} {platform.release()}. Synthetic records only.", "",
          "| Step | Result | Detail |", "| --- | --- | --- |"]
    md += [f"| {s['step']} | {s['result']} | {s['detail']} |" for s in report["steps"]]
    md += ["", "Overall: " + ("all steps passed." if report["passed"] else "at least one step failed."),
           "When this was written the network had been switched off, and the three tests above show no route to the internet."
           if offline else "The network was on, so this is not an offline run."]
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(report, indent=1), encoding="utf-8")
    say(f"\n{'ALL PASSED' if report['passed'] else 'SOME STEPS FAILED'}. Report written to {out}. Done: turn Wi-Fi back on.")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
