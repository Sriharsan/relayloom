# Optional Meta adapter: implemented, live acceptance not run

28 October 2026. **No live provider call has been made for this implementation.**
All adapter tests replace transport with local functions. Account billing,
credit eligibility, the real model response and an end-to-end video remain gates.

## Explicit activation boundary

The default `python -m relayloom` command never selects the Meta worker, even if
an API key is present. The application does not automatically load `.env` files.
After separate approval for actual inference and confirmation of usable access,
an operator may set the environment variables documented in `.env.example` and
use `--enable-meta-synthetic` with a separate workroom database, for example:

```sh
python -m relayloom --enable-meta-synthetic --database data/meta-workroom.sqlite3
```

This command can make billable calls when a permitted participant runs the
specialists. It does not claim credits, activate billing or send a startup ping.
Only the reviewed official Meta HTTPS endpoint is allowed. The key remains
server-side. Ambient HTTP proxies and redirects are disabled for that transport.

## Public synthetic fixture only

In Meta mode the exact shared brief must be:

> Draft a fictional refund policy for the Relayloom demo store.

Audience must be `Customers`, `Members` or `Trial customers`; refund days must
be an integer from 0 to 365. Any other brief/audience is rejected before a call
reservation. Participant names, room titles, cookies and invitation secrets are
never included in model requests. Dependency data comes only from this fixture's
previously validated specialist output. No customer uploads or arbitrary tools
are exposed. `store: false` is requested; it is not a zero-retention guarantee.

## Controls and accounting

- Two bounded request slots; dependent work waits without inference.
- No automatic retry, including timeouts, rate limits and server failures.
- One stable request identity per room/revision/role. Replaying that identity
  cannot dispatch again, even after restarting the local process.
- SQLite reserves before dispatch. Default maximum is six request attempts
  across the ledger; the policy cannot be silently raised on an existing ledger.
- Every reservation permanently consumes a slot. Missing/invalid usage, timeout
  or crash leaves an unknown hold. Unknown does not mean free or zero usage.
- The counter named `model_calls` is a conservative **reserved attempt count**;
  a crash between reservation and transport can leave an undispatched hold.
- Requests bound total completion/reasoning output through the documented
  `max_completion_tokens` field. The socket timeout is 20 seconds by default,
  limited to 30; it is not a universal wall-clock deadline for a slow peer.
- Valid reported prompt/completion/total tokens are recorded. Observing output
  tokens above the requested bound halts further ledger dispatches.
- Actual provider-billed dollars remain `null`. These controls are a durable
  attempt cap, **not a dollar cap or a guaranteed provider invoice bound**.
- JSON schema constrains the response, and the controller independently checks
  its structure, current policy, scope and dependency provenance before use.
- Provider prompts use the same scoped input selector as reuse fingerprints:
  Product receives only brief/audience; Engineering receives only refund days;
  Support receives the full intent and both dependency outputs. An omitted
  fingerprint field cannot silently influence a reused model summary.

The workroom database pins mode and worker configuration. A rehearsal database
cannot reopen in Meta mode and present its old outputs as model-generated.
Keep the Meta ledger at a different absolute path from the workroom database.
Do not delete or replace ledgers to bypass held requests; review unknown entries
and provider records before deciding whether a new authorized experiment is safe.

## Live acceptance check (not run)

`scripts/check_meta.ps1 --i-have-credit` (or `sh scripts/check_meta.sh --i-have-credit`)
runs `scripts/check_meta.py`. Without the flag it prints REFUSED and sends
nothing. With the flag it checks, printing PASS or FAIL per case: refusal
without `MODEL_API_KEY` (variable names only, no values), a complete
environment, a redacted worker representation, exactly one live Product
request on the public fixture, refusal of a replayed request identity, and
one ledger attempt with known reported usage. Offline tests in
`tests/test_meta_checks.py` cover these paths with fake transports. The
attempt cap is bounded by `max_attempts_ceiling` in `relayloom/policy.json`.

## Primary references checked

- [Meta overview and Standard model identifiers](https://dev.meta.ai/docs/overview)
- [Chat completion protocol and response usage](https://dev.meta.ai/docs/protocols/chat-completions)
- [Structured JSON output](https://dev.meta.ai/docs/cookbook/structured-output)
- [Request, output cap and usage schemas](https://dev.meta.ai/docs/api-reference/chat-completions/schemas)

The adapter uses a small standard-library HTTP client rather than copying an SDK
or private implementation. References establish the documented protocol; they
do not establish that this account has credits or that a live request passed.
