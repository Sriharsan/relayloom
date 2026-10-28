# Build plan and acceptance gates

Updated 28 October 2026. Checked items refer to the local synthetic rehearsal;
they do not establish live Meta functionality or hosted production readiness.

## Implementation order

- [ ] Confirm eligible build-start interpretation and account/model access.
- [x] Add reproducible local setup and synthetic fixtures.
- [x] Implement shared intent revisions and explicit task dependency state.
- [ ] Run two substantive Meta-backed specialists in parallel.
- [x] Propagate a second participant's constraint change without losing history (controller tests; browser acceptance separate).
- [x] Preserve valid work and reject stale local artifact publication; external destination integration remains future work.
- [ ] Add permission, usage reservation, retry and reconciliation controls.
- [ ] Connect a polished workroom and outcome view to actual state.
- [ ] Verify clean checkout, error paths and a three-minute demonstration.

Implemented permission and local publication checks do not establish a provider
budget cap, request reconciliation or independent external-business verification.
The current suite and explicit remaining gates are in IMPLEMENTATION.md.

## Required evidence

| Gate | Observation |
| --- | --- |
| Parallel work | Independent tasks overlap; dependent work starts after prerequisites |
| Efficient waiting | Waiting/restart causes no repeated model inference |
| Changed intent | New revision invalidates affected work; old results cannot authorize effects |
| Valid reuse | Reused output matches relevant inputs, configuration, freshness and authority |
| Shared work | Two authenticated participants see coherent state and attributable decisions |
| Permissions | Revocation, viewer status and workspace isolation apply server-side |
| Budget | Concurrent reservations cannot exceed the configured cap; unknown charges remain visible |
| Recovery | Crash/timeout after an effect reconciles without repeating it |
| Outcome | Destination records/tests substantiate completion independently of model claims |
| Honest measurement | Model usage and interventions recorded; comparable baselines clearly defined |
| Reproducibility | Public checkout runs submitted functionality without private source |
| Provenance | Each demonstrated new feature maps to dated commits and evidence |

Use deterministic fixtures for controller regression; label them as such. Run
small authorized live probes only after billing is verified. Do not silently
turn a failed check into a success or count an unrun case as passed.
