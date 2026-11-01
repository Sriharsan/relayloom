"""Run inside the agents container on the internal network. Proves what can and cannot leave.

1. A direct connection to the internet fails (the network has no route out).
2. Through the gateway, a host not in the policy is refused, and the refusal is logged.
3. The five demo cases run inside, in rehearsal mode, with the built in ledger.
Writes /logs/boundary_result.json.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

LOG = Path(os.environ.get("GATEWAY_LOG", "/logs/gateway.jsonl"))
results = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "checks": []}


def check(label, ok, detail=""):
    results["checks"].append({"check": label, "result": "PASS" if ok else "FAIL", "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}", flush=True)


def direct(host, port=443):
    try:
        socket.create_connection((host, port), timeout=5).close()
        return "connected"
    except OSError as error:
        return f"{type(error).__name__}: {error}"


for target in ("1.1.1.1", "8.8.8.8", "example.com"):
    outcome = direct(target)
    check(f"direct connection to {target} fails", outcome != "connected", outcome)

proxy = os.environ["HTTPS_PROXY"].split("//")[1]
host, port = proxy.split(":")
before = len(LOG.read_text().splitlines()) if LOG.exists() else 0
for target in ("example.com", "huggingface.co"):
    with socket.create_connection((host, int(port)), timeout=10) as s:
        s.sendall(f"CONNECT {target}:443 HTTP/1.1\r\nHost: {target}:443\r\nX-Relayloom-Case: boundary-probe\r\n\r\n".encode())
        reply = s.recv(200).decode(errors="replace").splitlines()[0]
    check(f"gateway refuses {target}", "403" in reply, reply)
time.sleep(0.5)
logged = [json.loads(line) for line in LOG.read_text().splitlines()[before:]] if LOG.exists() else []
check("every refusal is in the gateway log", sum(1 for e in logged if e["decision"].startswith("blocked")) >= 2,
      f"{len(logged)} new log lines")

done = subprocess.run([sys.executable, "-m", "relayloom.ap.cases", "all", "--data", "/tmp/ap"], capture_output=True, text=True)
print(done.stdout[-4000:], done.stderr[-1500:], flush=True)
results["cases_output"] = done.stdout
check("five demo cases pass inside the boundary (rehearsal mode, built in ledger)", done.returncode == 0)
results["passed"] = all(c["result"] == "PASS" for c in results["checks"])
Path("/logs/boundary_result.json").write_text(json.dumps(results, indent=1))
sys.exit(0 if results["passed"] else 1)
