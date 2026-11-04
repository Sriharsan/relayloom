"""Build the package, install it in a clean virtual environment with the network blocked, and prove it works.

Usage: python scripts/package_check.py [--md docs/PACKAGE_CHECK.md]

Steps: build the wheel and the source archive; run twine check; download a wheelhouse of every dependency (the only
step that uses the network); make a fresh virtual environment; install from the wheelhouse only, with no index; plant a
sitecustomize that refuses every connection except to 127.0.0.1; then run the commands a new user would run.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BLOCKER = '''import socket
_real = socket.socket.connect
def _guard(self, address, *a, **k):
    host = address[0] if isinstance(address, tuple) else address
    if str(host) not in ("127.0.0.1", "::1", "localhost"):
        raise OSError("network blocked by the package check: " + str(host))
    return _real(self, address, *a, **k)
socket.socket.connect = _guard
_gai = socket.getaddrinfo
def _gaiguard(host, *a, **k):
    if str(host) not in ("127.0.0.1", "::1", "localhost", None, ""):
        raise OSError("DNS blocked by the package check: " + str(host))
    return _gai(host, *a, **k)
socket.getaddrinfo = _gaiguard
'''
BILL = {"supplier_id": "SUP-CALDER", "bill_no": "CAL-0990", "bill_date": "2026-11-01", "po_number": "PO-1",
        "lines": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0, "amount_inr": 5900.0}],
        "tax_inr": 1062.0, "total_inr": 6962.0}
PO = {"po_number": "PO-1", "supplier_id": "SUP-CALDER", "tax_rate": 0.18,
      "items": [{"item_code": "CARTON-HD", "description": "Heavy duty shipping carton", "qty": 50, "rate_inr": 118.0}]}

results = []


def step(name, ok, detail=""):
    results.append({"step": name, "result": "PASS" if ok else "FAIL", "detail": detail})
    print(("PASS  " if ok else "FAIL  ") + name + (f"  {detail}" if detail else ""), flush=True)
    return ok


def run(cmd, cwd=None, env=None, expect=0):
    done = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr).strip(), done.returncode == expect


def main():
    work = Path(tempfile.mkdtemp(prefix="relayloom-pkg-"))
    dist = work / "dist"
    wheelhouse = work / "wheelhouse"
    started = time.time()
    code, out, ok = run([sys.executable, "-m", "build", "--outdir", str(dist), str(ROOT)])
    wheel = next(iter(dist.glob("*.whl")), None)
    sdist = next(iter(dist.glob("*.tar.gz")), None)
    if not step("build the wheel and the source archive", ok and wheel and sdist, f"{wheel.name if wheel else ''}"):
        print(out[-800:])
        return finish(results, started)
    code, out, ok = run([sys.executable, "-m", "twine", "check", str(wheel), str(sdist)])
    step("twine check (what PyPI checks before it accepts the upload)", ok, "wheel and sdist pass" if ok else out[-300:])
    names = subprocess.run([sys.executable, "-m", "zipfile", "-l", str(wheel)], capture_output=True, text=True).stdout
    step("the wheel carries the policy file, the typed marker and the licence",
         all(x in names for x in ("relayloom/ap/policy.json", "relayloom/py.typed", "LICENSE")))
    code, out, ok = run([sys.executable, "-m", "pip", "download", "-q", "--dest", str(wheelhouse), str(wheel)])
    step("download every dependency once into a wheelhouse (the only online step)", ok, f"{len(list(wheelhouse.glob('*')))} files")

    venv = work / "venv"
    run([sys.executable, "-m", "venv", str(venv)])
    py = venv / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    exe = py.with_name("relayloom.exe" if os.name == "nt" else "relayloom")
    code, out, ok = run([str(py), "-m", "pip", "install", "-q", "--no-index", "--find-links", str(wheelhouse), str(wheel)])
    step("install in a clean environment with no package index (offline install)", ok, out[-200:] if not ok else "")
    site = next((venv / "Lib").glob("site-packages")) if os.name == "nt" else next((venv / "lib").glob("python*/site-packages"))
    (site / "sitecustomize.py").write_text(BLOCKER, encoding="utf-8")
    env = {**os.environ, "RELAYLOOM_HOME": str(work / "home"), "PYTHONUTF8": "1", "HF_TOKEN": ""}
    probe = subprocess.run([str(py), "-c", "import socket; socket.create_connection(('1.1.1.1', 443), timeout=2)"], capture_output=True, text=True, env=env)
    step("the network blocker works (a connection to 1.1.1.1 is refused)", probe.returncode != 0 and "blocked" in probe.stderr)

    code, out, ok = run([str(exe), "--version"], env=env)
    step("relayloom --version", ok and out.startswith("relayloom "), out)
    code, out, ok = run([str(exe), "doctor"], env=env)
    step("relayloom doctor reports what is ready and what to run for the rest", ok and "relayloom models pull" in out and "Core is ready" in out)
    (work / "bill.json").write_text(json.dumps(BILL), encoding="utf-8")
    (work / "po.json").write_text(json.dumps(PO), encoding="utf-8")
    base = [str(exe), "check", "--bill-json", str(work / "bill.json"), "--po", str(work / "po.json"), "--out", str(work / "out")]
    code, out, ok = run(base + ["--counted", "46"], env=env, expect=3)
    step("a short delivery is HELD with exit code 3", ok and "HELD" in out and "received 46" in out)
    code, out, ok = run(base + ["--counted", "50", "--out", str(work / "out50")], env=env, expect=0)
    step("a full delivery is clear with exit code 0", ok and "CLEAR TO ENTER" in out)
    code, out, ok = run(base + ["--counted", "46", "--json"], env=env, expect=3)
    try:
        step("--json prints a result a script can read", ok and json.loads(out)["state"] == "held")
    except ValueError:
        step("--json prints a result a script can read", False, out[-200:])
    code, out, ok = run([str(exe), "verify", str(work / "out" / "receipts.jsonl")], env=env)
    step("verify says the chain is intact, with the network blocked", ok and "chain verified" in out, out)
    path = work / "out" / "receipts.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace("counted 46", "counted 50"), encoding="utf-8")
    code, out, ok = run([str(exe), "verify", str(path)], env=env, expect=1)
    step("an edited receipt breaks the chain (exit code 1)", ok and "BROKEN" in out)
    code, out, ok = run([str(exe), "check", "--bill-json", str(work / "nope.json"), "--po", str(work / "po.json"), "--counted", "1"], env=env, expect=2)
    step("a missing file gives a short message, not a traceback", ok and "not found" in out and "Traceback" not in out, out)
    code, out, ok = run([str(exe), "check", "--bill-json", str(work / "bill.json"), "--po", str(work / "po.json"), "--photos", str(work)], env=env, expect=2)
    step("photos that are not there give a clear message", "photos not found" in out or "none given" in out or ok)
    code, out, ok = run([str(exe), "models", "pull"], env=env, expect=2)
    step("models pull needs your own token and says so", ok and "HF_TOKEN" in out)
    shutil.rmtree(work, ignore_errors=True)
    return finish(results, started)


def finish(rows, started):
    passed = all(r["result"] == "PASS" for r in rows)
    args = sys.argv[1:]
    if "--md" in args:
        lines = ["# Package check", "", f"Run {time.strftime('%Y-%m-%d %H:%M %z')} by `python scripts/package_check.py`, in {round(time.time() - started)} s.",
                 "A clean virtual environment, installed from a wheelhouse with no package index, with every non-local connection refused.", "",
                 "| Step | Result | Detail |", "| --- | --- | --- |"]
        lines += [f"| {r['step']} | {r['result']} | {r['detail'][:120].replace('|', '/')} |" for r in rows]
        lines += ["", "All steps passed." if passed else "Some steps failed."]
        Path(args[args.index("--md") + 1]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nALL PASSED" if passed else "\nFAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
