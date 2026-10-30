# Relayloom: Meta Global AI Developer Hackathon submission notes

Startup track. Submissions due 4 November 2026, 9:00 PM US Eastern
(5 November, 7:30 AM IST). Author: Sriharsan B S, the only contributor.

## Deliverables and judging criteria: pending official guide read

The participant guide has not been read for this file. Deliverables, required
fields, video length rules and judging criteria will be filled in from the
official guide. Nothing below should be read as matching those rules yet.

## What Relayloom is

A shared workroom where people and AI specialists work on one goal in
parallel. When someone changes the goal, Relayloom keeps the work that is
still valid, redoes only what the change touched, refuses late results from
the old goal, and publishes only after a recorded owner approval and a check
of the outcome.

## What runs today

| Area | Status |
| --- | --- |
| Shared workroom, roles, one-time invites | Runs locally. Tested. |
| Parallel specialists, dependency waiting | Runs locally with deterministic rehearsal outputs. Tested. |
| Selective reuse after an intent change | Runs locally. Tested. |
| Stale output rejection | Runs locally. Tested. |
| Autonomy policy file, approval record, run limits, outcome check | Runs locally. Tested. See [docs/AUTONOMY.md](docs/AUTONOMY.md). |
| Meta adapter (Chat Completions, structured output, attempt ledger) | Built and offline tested with fake transports. **Never run against the Meta API.** |
| Live Meta acceptance check | `scripts/check_meta.ps1 --i-have-credit`. Not run. Waits for billing. |

## How to run

```sh
python -m relayloom --port 8800
```

Open http://127.0.0.1:8800. Python 3.11 or later, nothing to install.
`scripts/check_demo.ps1` prints PASS or FAIL for each rehearsal step.

## Use of Meta models

Planned: a Muse Spark Standard model for scoped specialist drafts on a fixed
public fixture. The adapter, limits and ledger are in `relayloom/meta.py` and
[docs/META.md](docs/META.md). No live call has been made, so no Meta model
output, latency or cost is reported anywhere in this repository.

## Built during the event

See [docs/HACKATHON_UPDATES.md](docs/HACKATHON_UPDATES.md). Every commit is
after the 26 October kickoff; the eligible build start is not confirmed.

## Links

- Repository: https://github.com/Sriharsan/relayloom
- Video: not recorded yet. Script: [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)

## Blocked on the founder

- Billing and credit on the Meta developer account, then one run of
  `scripts/check_meta.ps1 --i-have-credit` with `MODEL_API_KEY`,
  `RELAYLOOM_META_ENDPOINT`, `RELAYLOOM_META_MODEL`, `RELAYLOOM_META_LEDGER`
  and `RELAYLOOM_SYNTHETIC_ONLY` set in the local environment.
- Reading the official participant guide to fill the pending section above.
- Recording the video.
