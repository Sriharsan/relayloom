# Product and architecture

## The user problem

People and agents lose time when goals change during execution. They need to
know which result is current, which work can be kept, and which action is safe
to continue under the permission already granted.

## Initial product contract

One workroom holds the current intent revision, constraints, participants,
explicit scope and task dependencies. Independent specialists can run together.
A blocked specialist waits for an event instead of repeatedly inferring.

Each output records its inputs, goal revision, relevant configuration and
authority. A new requirement invalidates affected outputs; unrelated work may
be retained only when those checks still hold. Cancellation alone is not a
guarantee that a late external effect cannot happen.

Meta models propose plans and scoped work. The controller validates structure,
permissions, dependency status, cost and destination outcome. Reviews may disagree;
votes are evidence, not proof of correctness or authority.

## Proposed components

| Component | Responsibility |
| --- | --- |
| Shared workroom | Authenticated participants, goal revisions, decisions and handoffs |
| Dependency scheduler | Parallel ready tasks, durable waiting and bounded wakeup |
| Model adapter | Meta requests, validated responses and measured usage |
| Validity controller | Input/configuration/authority provenance and stale-result rejection |
| Scoped executor | Approved tool calls, destination reconciliation and outcome receipts |
| Evidence view | Current state, disagreement, final checks and actual cost |

These are architecture intentions, not claims of implemented modules.

## Design contract

Use a compact live workroom and a focused outcome view. Persistent navigation,
readable agent states and contextual drawers should replace long report-like
forms. Show waiting reasons, current revision, next action and participants.
Run detail should connect events, latency and usage to the final outcome.

Provide accessible keyboard controls, readable type, clear focus, empty/error/
disconnected states and responsive layouts. Never invent counters, savings or
customer logos to make a screen look active.

## Expansion

## One connected operating loop

The intended system connects shared human intent to specialist planning,
parallel execution, security checks, scoped action, outcome verification and
governed improvement. These components share task identity, intent revision,
permissions, evidence and budget; they are not disconnected demonstrations.
Independent work runs in parallel. Dependent work waits for verified inputs.

Live participants guide the same workroom. Security AI evaluates supported
threats and proposed actions while enforced policy controls access and effects.
Continuous operations preserve state and recover within approved limits. Local
intelligence and infrastructure follow explicit data-routing and resource rules.

Improvement closes the loop: observed failure -> proposed change -> isolated
evaluation -> held-out/regression checks -> authorized promotion or rejection ->
monitored outcome. Recursive capability improvement is the long-term ambition;
it requires repeated measured gains and cannot bypass immutable authority or
rewrite its own acceptance criteria to declare success.

This is the integrated product direction. The current public repository remains
a planning scaffold; none of these paragraphs establishes implementation.

Continuous incident/recovery loops, additional supported integrations, local
intelligence and governed improvement extend the same contract. Before/after-
production support requires concrete destination and rollback integration.
Third-party credential rotation is vendor-specific. Recursive improvement needs
held-out evidence, regression refusal and explicit promotion authority.
