# Package check

Run 2026-11-04 11:50 +0530 by `python scripts/package_check.py`, in 150 s.
A clean virtual environment, installed from a wheelhouse with no package index, with every non-local connection refused.

| Step | Result | Detail |
| --- | --- | --- |
| build the wheel and the source archive | PASS | relayloom-0.3.0-py3-none-any.whl |
| twine check (what PyPI checks before it accepts the upload) | PASS | wheel and sdist pass |
| the wheel carries the policy file, the typed marker and the licence | PASS |  |
| download every dependency once into a wheelhouse (the only online step) | PASS | 18 files |
| install in a clean environment with no package index (offline install) | PASS |  |
| the network blocker works (a connection to 1.1.1.1 is refused) | PASS |  |
| relayloom --version | PASS | relayloom 0.3.0 |
| relayloom doctor reports what is ready and what to run for the rest | PASS |  |
| a short delivery is HELD with exit code 3 | PASS |  |
| a full delivery is clear with exit code 0 | PASS |  |
| --json prints a result a script can read | PASS |  |
| verify says the chain is intact, with the network blocked | PASS | 6 receipts: chain verified |
| an edited receipt breaks the chain (exit code 1) | PASS |  |
| a missing file gives a short message, not a traceback | PASS | relayloom: bill not found: C:\Users\bssri\AppData\Local\Temp\relayloom-pkg-qowxrete\nope.json |
| photos that are not there give a clear message | PASS |  |
| models pull needs your own token and says so | PASS |  |

All steps passed.
