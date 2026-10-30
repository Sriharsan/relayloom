# Autonomy with explicit approval

Autonomy where it is safe, explicit approval where it matters, proof after
every action. This page maps that rule to code and tests. It describes the
local rehearsal; live Meta inference has not been run.

## Levels come from a file, not from a prompt

[`relayloom/policy.json`](../relayloom/policy.json) is read once when the
server starts. `load_policy` in `relayloom/controller.py` refuses to start if
an operation is missing, declared at the wrong level, or given limits outside
reviewed bounds. Nothing in a request, intent text or model output is read as
policy.

| Operation | Level | Limit |
| --- | --- | --- |
| Explain what changed (the loom) | Assist | Takes no action |
| Specialist drafts | Draft | Draft only, no external effect |
| Run ready specialists | Execute within limits | 9 runs per revision, no automatic retry |
| Meta API request | Execute within limits | Attempt ledger, ceiling 20, default 6, no automatic retry |
| Publish the artifact | Execute with approval | Owner approval per revision, one local artifact |

## The approval record

Ticking "Approve publication of this revision" writes a row to the
`approvals` table: approver, operation `publish_artifact`, revision, time,
the limit approved and a digest of the intent approved. Publication refuses
with HTTP 403 unless an active record matches the current revision and intent.
Changing the intent starts a new revision, so an old approval no longer
applies. The published artifact carries a copy of its approval record.

The workroom shows three steps: Request, Decision and Outcome. The activity
log records the grant, the publication and the outcome check.

## Proof after the action

After publishing, `verify_publication` reads the stored artifact back and
compares it with its approval record: same revision and action, same intent,
scope inside the approved limit, exactly one artifact, outputs equal to the
recorded specialist work. The result is stored as:

- `VERIFIED`: every comparison passed. Only then does the UI say "Verified outcome".
- `FAILED`: a comparison failed. The reason is shown.
- `UNKNOWN`: the check could not complete. Publishing again never re-executes;
  it only repeats the read-only check (reconciliation).

## Inside the limits

Specialist runs proceed on their own. When a revision reaches its run limit,
the next specialist is not started, its card says why, an `escalated` event is
recorded, and further run requests get HTTP 429. Failed work is retried only
when a person asks. In Meta mode a timeout or missing usage leaves the attempt
held as unknown and is never retried automatically.

## Status of each point

| Requirement | Status | Evidence |
| --- | --- | --- |
| Levels per operation in a policy file outside the model | Added 30 Oct | `policy.json`, `test_policy_file_declares_a_level_for_every_operation` |
| Approval is an explicit record (who, what, when, limit) | Added 30 Oct. Before, a boolean permission flag and an event existed. | `test_every_published_artifact_has_its_approval_record_and_verified_outcome` |
| Action blocked without approval | Already true for the flag, now tied to the record | `test_publication_blocked_without_approval_record`, existing `test_csrf_and_viewer_cannot_mutate`, `test_selective_reuse_and_idempotent_current_publication` |
| Action blocked above a limit | Already true for Meta attempts; added for runs | existing `test_atomic_slots_across_independent_ledger_connections`, new `test_attempt_ledger_cap_refuses_further_dispatch`, `test_runs_blocked_above_policy_limit_and_escalated` |
| Approval record present for every executed approval-level action | Added | same test as above checks every artifact row |
| UNKNOWN never retried blindly | Already true for Meta; added for publication outcomes | existing `test_timeout_is_unknown_held_and_never_retried`, new `test_unknown_outcome_is_reconciled_by_reading_never_by_republishing` |
| Changed prompt cannot change a limit | Added | `test_changed_intent_text_cannot_change_a_limit_or_skip_approval`; the Meta ledger refusing a raised cap on an existing ledger was already tested in `test_atomic_slots_across_independent_ledger_connections` |
| Outcome checked against the record | Added | `test_tampered_artifact_fails_outcome_check_and_replay_does_not_republish` |
| Shown in UI, log, README and video kit | Added | Autonomy policy panel, Approval and proof steps, `docs/VIDEO_SCRIPT.md` |

Not done: approvals for operations other than publication (none of the other
operations has an external effect today), approval expiry by time, and any
live Meta run of the "within limits" path.
