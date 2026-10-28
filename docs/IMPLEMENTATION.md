# Implementation checkpoint

28 October 2026, Asia/Kolkata. Source is new public event work. Parent release
review records the final commit; no private implementation or history was copied.

## Working foundation

- Standard-library HTTP delivery and SQLite transactions; no runtime dependency
  installation. Bound to loopback, with Host/Origin checks, JSON limits, CSRF
  tokens and HttpOnly/SameSite sessions.
- Workroom-scoped owner/editor/viewer membership. One-use, 30-minute invites;
  eight-hour sessions; logout deletes the matching server session.
- Server-Sent Events with session/membership rechecks and a 12-stream limit.
  State snapshots contain only the caller's room and its latest 100 events.
- Two bounded worker slots. Product and Engineering can run together; Support
  runs after both pass their output contract. Waiting never invokes a worker.
- Transactional intent revisions and current-revision publication permission.
  New intent invalidates affected work and revokes the older publication grant.
- Reuse keys bind relevant inputs, worker configuration and draft-only scope.
  Refund changes retain completed Product work; audience changes retain
  completed Engineering work. Support binds both dependency output digests.
- Late results are discarded. Publication rechecks output contracts, provenance,
  current intent, role and permission in one SQLite transaction. The unique
  room/revision artifact key makes publication replay idempotent.
- Interrupted RUNNING tasks become FAILED on restart and require an explicit
  run request. Sessions, revisions, evidence and artifacts remain in SQLite.

## Verification

`python -m unittest discover -s tests -v` passed **27 tests** on Python 3.13.3
on 28 October. These use synthetic records and real temporary SQLite databases
and loopback HTTP connections. Initial task insertion had a column-count error;
the tests exposed it, the insertion was corrected, and the suite passed. A later
expanded run exposed scheduler shutdown racing Windows database cleanup; close
now joins scheduler threads before releasing the worker pool. Wake requests are
coalesced so a request at scheduler exit is not lost. The final suite passed.

A clean temporary copy containing only `relayloom/`, `web/` and `tests/` initially
passed all 16 controller tests, with no installed project package or private files. This
probe exposed a Windows unread-body reset on a 413 response; bounded draining
of small rejected bodies corrected it before the final clean-copy pass.

No provider calls, credit claims, external customer mutations or billing changes
were made. Rehearsal model calls are zero. UI visual/device acceptance and final
clean-checkout integration are parent release gates, not implied by these tests.

The optional Meta worker adds eleven offline tests: explicit configuration,
fixture-only routing, structured requests, usage validation, persistent replay
refusal, unknown timeout holds, observed overrun stop, malformed output rejection,
concurrent durable reservation and controller mode pinning. Its transport is
replaced by local functions throughout the suite. See META.md for precise limits.

Parent review found that Meta prompts originally contained full intent although
Product/Engineering reuse keys scoped only relevant fields. Both now share one
input selector, and the prompt configuration version is bumped. The added test
proves irrelevant changes preserve identical payloads and fingerprints, while
relevant changes alter both. No network calls were used for this correction.

The final clean temporary copy also passed all 27 controller/HTTP/offline-adapter
tests. No private source or installed project package was needed.

## Remaining gates

Parent browser acceptance on28October used separate127.0.0.1/localhost cookie
contexts against one server: owner created workroom, Product/Engineering ran
together, Support waited, editor joined, changed30->14days, Product was reused,
Engineering/Support reran, owner authorized/published revision2 and editor saw
the same artifact. No inference or external action occurred. Final result view
shows policy/response and four checks; exact JSON is collapsed. Laptop layout
keeps goal, agents and selected evidence side by side with bounded evidence.

Nine persistent offline UI tests cover stale session/refresh/stream/mutation
responses, signout clearing, private invite clearing, readable expiry, human
outcome/closed evidence, prior artifact distinction and older same-revision
event rejection. They test state behavior, not every device's visual layout.
Public CI runs these plus the27 Python tests onLinux/Windows without keys.

1. Live acceptance of the implemented Meta adapter, including account access,
   actual response/latency/usage and the intended request budget policy.
2. An authorized end-to-end Meta demonstration and measured usage ledger.
3. Independent user/keyboard/responsive acceptance and final public-source review.
4. Event timing interpretation, final three-minute video and submission fields.
5. Hosted deployment identity/abuse/TLS controls before remote internet access.

The current build does not execute arbitrary code, integrate with customer
systems, rotate vendor credentials, or improve its own capability recursively.
Those directions need concrete adapters, protected evaluations and scoped
promotion authority. They remain part of the broader operating-system vision.
