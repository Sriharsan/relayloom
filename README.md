# Relayloom

### Change direction. Keep the useful work.

Relayloom is a shared workroom for people and autonomous AI teams. Its goal is
to let specialists work in parallel, keep everyone aligned when instructions
change, and verify that the final result matches the current goal.

Today, changing one requirement can mean repeating context, restarting agents
and manually checking conflicting outputs. Relayloom is being built to retain
valid work, redo only affected tasks and prevent outdated results from taking
action. We will measure the effect on completed work, supervision and cost.

**Status: initial public planning scaffold for the Meta Global AI Developer
Hackathon, Startup track. No executable application or measured savings yet.**

## The experience we are building

1. People share a goal, constraints and explicit permissions in one workroom.
2. Meta-powered specialists work on independent tasks in parallel; dependent
   tasks wait without repeatedly calling a model.
3. A participant changes a requirement. The plan records a new revision and
   identifies which outputs remain valid.
4. Affected work is revised. Outdated results cannot authorize a change.
5. The team sees the outcome, evidence, remaining exceptions and actual usage.

The first demonstration will use synthetic product, engineering and support
work. That is a testable starting point for continuous work across supported
business systems, rather than a claim of universal integrations.

## Meta models

The proposed default is Muse Spark 1.3 Standard for interpreting goals, proposing
dependency updates and performing scoped specialist work. Stronger-model
escalation will be bounded and evaluated. Deterministic controls will enforce
permissions, budgets, revision validity and final checks.

API access and live integration have not yet been verified. Recorded or simulated
results will be labelled, and will not be presented as live Meta inference.

## Read the project

- [Product and architecture](docs/PRODUCT.md)
- [Build plan and acceptance gates](docs/BUILD_PLAN.md)
- [Hackathon contribution record](docs/HACKATHON_PROVENANCE.md)
- [Three-minute demo plan](docs/DEMO.md)
- [Official resources](docs/RESOURCES.md)
- [Security and privacy boundaries](SECURITY.md)

No installation command is provided yet because this commit contains planning
documents only. A runnable clean-checkout guide will accompany implementation.

## Broader direction

Shared live work, multi-agent coordination, continuous operations, local
execution, security, privacy, recovery and cost control belong together. Longer
term, improvement proposals should be tested against protected acceptance checks
before promotion. General recursive self-improvement remains research, not a
capability claimed by this scaffold.

## Contribution and reuse

Original project work is authored by Sriharsan B S. Third-party material, if
introduced, must retain its own license and attribution. Public availability is
not a claim that every dependency or concept originated here. See the dated
contribution record for the boundary between prior work and event-built work.
