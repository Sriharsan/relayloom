# Relayloom

### Change direction. Keep the useful work.

Relayloom is a shared workroom where people and AI specialists work on one goal
in parallel. When someone changes a requirement, it keeps the work that is still
valid, redoes only what the change touched and checks the final result against
the current goal.

```sh
python -m relayloom --port 8800
```

Then open http://127.0.0.1:8800. Python 3.11 or later, nothing to install.

Today, changing one requirement can mean repeating context, restarting agents
and manually checking conflicting outputs. Relayloom is being built to retain
valid work, redo only affected tasks and prevent outdated results from taking
action. We will measure the effect on completed work, supervision and cost.

**Status: runnable local rehearsal for the Meta Global AI Developer Hackathon,
Startup track. The controller and shared workroom work with synthetic specialist
outputs. Live Meta inference and measured customer savings are not claimed.**

## Try the workroom

Install Python 3.11 or later, clone this repository, and run from its root:

```sh
python -m relayloom --port 8800
```

Open **http://127.0.0.1:8800**. No package installation, API key, Docker,
payment method or network inference is needed. The tested interpreter is
Python 3.13.3. This checkout command serves the included `web/` files.

1. Create a workroom with a synthetic goal. You become its owner.
2. Create an editor or viewer invite. Use a separate browser profile to join;
   an invite is single-use and expires after 30 minutes.
3. Run the specialists. Product and Engineering start together; Support waits
   for both outputs. The workroom shows real server state and events.
4. Change only the refund window. Completed Product evidence can be retained;
   Engineering and Support need fresh work. Publication permission resets.
5. Complete the current work, allow publication, and publish its checked local
   artifact. Repeating publication creates no second artifact for that revision.

To see stale-output rejection, change the intent while Engineering is still
running. Its late output is discarded and current-revision work replaces it.
All records stay in the ignored `data/relayloom.sqlite3` file by default.
Use synthetic information only. This is a loopback rehearsal, not an internet
hosting service. Do not expose its port through a public proxy or tunnel.

## The operating contract

1. People share a goal, constraints and explicit permissions in one workroom.
2. Independent specialists work in parallel; dependent tasks wait without
   repeated worker calls. Current rehearsal outputs are deterministic.
3. A participant changes a requirement. The plan records a new revision and
   identifies which outputs remain valid.
4. Affected work is revised. Outdated results cannot authorize a change.
5. The team sees the outcome, evidence, remaining exceptions and actual usage.

The current demonstration uses synthetic product, engineering and support work.
It publishes a local artifact only; it does not change an external business
system. This is a testable foundation for supported continuous operations.

## Meta models

The proposed default is Muse Spark 1.3 Standard for interpreting goals, proposing
dependency updates and performing scoped specialist work. Stronger-model
escalation will be bounded and evaluated. Deterministic controls will enforce
permissions, budgets, revision validity and final checks.

An optional Meta adapter now supports the documented Chat Completions protocol,
structured specialist output and a durable request-attempt ledger. It is disabled
by default and offline-tested only. Nothing silently activates inference.
Rehearsal reports zero model calls. See [the explicit Meta boundary](docs/META.md)
for its fixed public fixture, limits and unrun live acceptance gate.

## Verify the controller

```sh
python -m unittest discover -s tests -v
node --test tests/ui.test.cjs
```

The tests exercise permission boundaries, two participants, session revocation,
one-time invites, concurrent specialists, dependency waiting, intent conflicts,
selective reuse, stale output, malformed evidence, checked publication, restart
recovery, and real HTTP request boundaries. See [the implementation checkpoint](docs/IMPLEMENTATION.md).

The offline suite currently passes 27 Python and 9 UI state tests. The founder's
local browser rehearsal also exercised separate owner/editor sessions, shared
revision changes, selective reuse, current work and owner-only publication.
These are synthetic rehearsal results, not live Meta or customer outcomes.

## Read the project

- [Product and architecture](docs/PRODUCT.md)
- [Build plan and acceptance gates](docs/BUILD_PLAN.md)
- [Hackathon contribution record](docs/HACKATHON_PROVENANCE.md)
- [Three-minute demo plan](docs/DEMO.md)
- [Official resources](docs/RESOURCES.md)
- [Security and privacy boundaries](SECURITY.md)
- [Optional Meta adapter and usage boundary](docs/META.md)

## Broader direction

Shared live work, multi-agent coordination, continuous operations, local
execution, security, privacy, recovery and cost control belong together. Longer
term, improvement proposals should be tested against protected acceptance checks
before promotion. General recursive self-improvement remains research, not a
capability claimed by this local build.

## Contribution and reuse

Original project work is authored by Sriharsan B S. Third-party material, if
introduced, must retain its own license and attribution. Public availability is
not a claim that every dependency or concept originated here. See the dated
contribution record for the boundary between prior work and event-built work.
