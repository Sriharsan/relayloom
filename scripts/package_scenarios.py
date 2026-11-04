"""Run every command line scenario and write the table to docs/PACKAGE_SCENARIOS.md.

Usage: python scripts/package_scenarios.py [--md docs/PACKAGE_SCENARIOS.md]
"""
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from scenarios import SCENARIOS, run_scenario  # noqa: E402

LABEL = {0: "clear to enter", 3: "held", 2: "could not run, clear message", 1: "chain broken, caught", None: "no crash"}


def main():
    rows, started = [], time.time()
    for group, name, spec, expected, phrase in SCENARIOS:
        t0 = time.perf_counter()
        code, text = run_scenario(group, name, spec, expected, phrase)
        ok = (expected is None or code == expected) and bool(re.search(phrase, text)) and "Traceback" not in text
        rows.append((group, name, LABEL.get(expected, str(expected)), "PASS" if ok else "FAIL", round((time.perf_counter() - t0) * 1000)))
        print(("PASS  " if ok else "FAIL  ") + f"[{group}] {name}  ({rows[-1][4]} ms)")
    passed = all(r[3] == "PASS" for r in rows)
    args = sys.argv[1:]
    if "--md" in args:
        lines = ["# Command line scenarios", "", f"Run {time.strftime('%Y-%m-%d %H:%M %z')} by `python scripts/package_scenarios.py`. {len(rows)} scenarios in five groups: "
                 "typical deliveries, varied inputs, extreme inputs, repeated and shared use, and damaged receipts. Each runs the real command in a fresh folder.", "",
                 "| Group | Scenario | Expected | Result | Time |", "| --- | --- | --- | --- | --- |"]
        lines += [f"| {g} | {n} | {e} | {r} | {ms} ms |" for g, n, e, r, ms in rows]
        lines += ["", f"{sum(r[3] == 'PASS' for r in rows)} of {len(rows)} passed in {round(time.time() - started, 1)} s."]
        Path(args[args.index("--md") + 1]).write_text("\n".join(lines) + "\n", encoding="utf-8")
        groups = {}
        for g, n, e, res, ms in rows:
            groups.setdefault(g, [0, 0])[0] += 1
            groups[g][1] += res == "PASS"
        (ROOT / "site-src" / "src" / "data" / "scenarios.json").write_text(json.dumps({"total": len(rows), "passed": sum(x[3] == "PASS" for x in rows),
            "groups": [{"group": g, "cases": n, "passed": ok} for g, (n, ok) in groups.items()]}, indent=1), encoding="utf-8")
    print(f"\n{sum(r[3] == 'PASS' for r in rows)} of {len(rows)} passed")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
