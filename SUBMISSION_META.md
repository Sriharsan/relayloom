# Relayloom: Meta Global AI Developer Hackathon submission notes

Startup track. Submissions due 4 November 2026, 9:00 PM US Eastern
(5 November, 7:30 AM IST). Author: Sriharsan B S, the only contributor.

## Deliverables, rules and judging

Source: the official participant guide,
https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details (sign in
needed), read 30 October 2026.

**Deliverables.** One project per team, submitted by one Representative on the
CV platform by Wednesday 4 November, 9:00 PM ET. A public repository and a
working link to a demo video of three minutes that highlights what was built
during the hackathon. The code and the live product are also judged.

**Rules that apply here.**

- The repository must be public. Solo teams are allowed.
- The demo must only highlight features built during the hackathon, and judges
  must be able to tell what was created then. Not identifying original
  contributions means disqualification.
- Startups may build on existing products but must clearly identify what was
  newly developed. Building period: 27 October to 4 November (ET).
- Use no code, data or assets without rights.
- The project must incorporate Meta's models: the Meta Model API (Muse Spark
  series and others), or Meta open weights (Muse Spark Open, Muse Glimmer), or
  Muse Code.
- Listed anti projects include basic RAG, simple chatbots and image analyzers.
  Relayloom is a coordination and approval workroom, not one of these.

**Judging.**

- Stage one, pass or fail: fits a theme and "reasonably used Meta Model API
  and/or Meta's open-weight models to build the project in the Hackathon".
- Stage two, scored 0 to 10: Impact 30%, Use of Meta AI Tooling 25%, Technical
  Depth and Execution 20%, Demo 25%.
- Stage three: the top 5 per track are ranked live from the videos.
- Relevant bonus: Best Agentic Use-Case (autonomy, effectiveness, usefulness),
  which matches the autonomy with approval work in
  [docs/AUTONOMY.md](docs/AUTONOMY.md). Best Build on Meta Open Weight Models
  is also open (Muse Spark Open or Muse Glimmer, own hardware or partner
  inference).

**Where Relayloom stands against stage one.** No Meta model has run yet. The
paid API path is built and offline tested but not run. Stage one needs a real
run, either through the Meta Model API once billing and credit are confirmed,
or through an open weight model. Until one of these actually runs, this
project does not claim Meta model use.

**Timing.** Commits `ec6dc51`, `4c13989` and `c6ea062` (26 October, 2:35 to
2:46 PM ET) are scope documents made after kickoff and before the building
period. The first code is `3668d31`, 28 October, 9:08 AM ET, inside the
building period. Details: [docs/HACKATHON_UPDATES.md](docs/HACKATHON_UPDATES.md).

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

See [docs/HACKATHON_UPDATES.md](docs/HACKATHON_UPDATES.md). All code is from
the building period (first code commit 28 October). Three documentation
commits from 26 October predate it and are labelled as such.

## Links

- Repository: https://github.com/Sriharsan/relayloom
- Video: not recorded yet. Script: [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)

## Blocked on the founder

- Billing and credit on the Meta developer account, then one run of
  `scripts/check_meta.ps1 --i-have-credit` with `MODEL_API_KEY`,
  `RELAYLOOM_META_ENDPOINT`, `RELAYLOOM_META_MODEL`, `RELAYLOOM_META_LEDGER`
  and `RELAYLOOM_SYNTHETIC_ONLY` set in the local environment.
- A real Meta model run (API or open weights) to pass stage one.
- Submitting on the CV platform by 4 November, 9:00 PM ET.
- Recording the video.
