"""Live Meta acceptance check. Makes ONE billable request, and only on request.

Run only after billing and credit are confirmed for the account:

    python scripts/check_meta.py --i-have-credit

Without --i-have-credit this script refuses and sends nothing. It never prints
the API key. Configuration comes from the environment variables named in
.env.example; this script does not read .env files.
"""
import argparse
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from relayloom.controller import Rejected  # noqa: E402
from relayloom.meta import MetaWorker, REQUIRED_ENVIRONMENT, SYNTHETIC_BRIEF, transport  # noqa: E402

FLAG = "--i-have-credit"
REFUSAL = ("REFUSED: this check sends one billable request to the Meta API. "
           f"Confirm billing and credit first, then re-run with {FLAG}. Nothing was sent.")


def run_checks(env, send=transport, out=print):
    """Return the list of (case, passed). `send` is replaceable only for offline tests."""
    results = []
    secret = str(env.get("MODEL_API_KEY", ""))

    def report(case, passed, detail=""):
        results.append((case, passed))
        line = f"{'PASS' if passed else 'FAIL'}  {case}" + (f"  ({detail})" if detail else "")
        if secret and secret in line:
            line = f"{'PASS' if passed else 'FAIL'}  {case}  (detail withheld)"
        out(line)

    # 1. Refusal without a key names only variable names.
    without_key = {name: value for name, value in env.items() if name != "MODEL_API_KEY"}
    try:
        MetaWorker.from_environment(without_key)
        report("refuses to start without MODEL_API_KEY", False, "worker was created")
    except ValueError as error:
        message = str(error)
        leaked = any(str(value) and str(value) in message for name, value in without_key.items()
                     if name in REQUIRED_ENVIRONMENT and len(str(value)) > 3)
        report("refuses to start without MODEL_API_KEY", "MODEL_API_KEY" in message and not leaked)

    # 2. The configured environment is complete and accepted.
    try:
        worker = MetaWorker.from_environment(env)
    except ValueError as error:
        report("environment configured", False, str(error))
        return results
    report("environment configured", True, f"model {worker.model}")
    report("worker representation hides the key", secret not in repr(worker))

    # 3. Exactly one live request for the Product role on the fixed public fixture.
    calls = []

    def counted(request, timeout):
        calls.append(1)
        return send(request, timeout)

    worker.send = counted
    room = f"check-meta-{int(time.time())}"
    identity = f"{room}:1:product"
    intent = {"brief": SYNTHETIC_BRIEF, "audience": "Customers", "refund_days": 30}
    try:
        result = worker.execute(identity, room, "product", intent, {})
        report("one live Product request returns validated output", True, f"summary of {len(result['summary'])} characters")
    except Rejected as error:
        report("one live Product request returns validated output", False, str(error))
    report("exactly one request was dispatched", len(calls) == 1, f"{len(calls)} dispatched")

    # 4. The same request identity cannot be sent again.
    try:
        worker.execute(identity, room, "product", intent, {})
        report("replayed request identity is refused", False, "a second request was accepted")
    except Rejected:
        report("replayed request identity is refused", len(calls) == 1, f"{len(calls)} dispatched in total")

    # 5. The durable ledger recorded the attempt and its reported usage.
    metrics = worker.metrics(room)
    report("ledger recorded one attempt", metrics["model_calls"] == 1,
           f"attempts {metrics['model_calls']}, unknown usage {metrics['unknown_usage_requests']}, "
           f"reported tokens {metrics['reported_total_tokens']}, slots left {metrics['attempt_slots_remaining']}")
    report("reported usage is known", metrics["unknown_usage_requests"] == 0)
    return results


def main(argv=None, env=None, send=transport, out=print):
    parser = argparse.ArgumentParser(description="One-request live Meta acceptance check.")
    parser.add_argument(FLAG, dest="confirmed", action="store_true",
                        help="Confirm billing and credit are in place. Sends one billable request.")
    args = parser.parse_args(argv)
    if not args.confirmed:
        out(REFUSAL)
        return 2
    results = run_checks(dict(os.environ) if env is None else env, send=send, out=out)
    failed = sum(not passed for _, passed in results)
    out(f"{len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
