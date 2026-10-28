# Security and privacy boundaries

This repository contains a local rehearsal, not an internet production service.
Do not put personal records, passwords, API keys or production data in issues,
commits, screenshots or demonstrations. Demonstration inputs must be synthetic.

The current controller enforces room-scoped session reads and mutations, live
membership checks on event streams, owner/editor/viewer authority, same-origin
request checks, CSRF tokens, bounded input, intent revisions, output provenance
and atomic idempotent local publication. See docs/IMPLEMENTATION.md and tests.

The server binds only to loopback. Invitations are bearer secrets: share them
only with the intended participant. They expire after 30 minutes and one use.
Sessions expire after eight hours and are deleted on logout. Display names are
self-asserted, not verified real-world identities. Keep the local data directory
private to your operating-system account. Do not run multiple controllers on one
database or expose this service through a public tunnel or proxy.

Optional Meta mode requires both a CLI switch and explicit environment values.
Only the bundled public fictional fixture may reach the reviewed Meta endpoint.
It has no tools, retries, redirect forwarding or customer-upload route. Durable
attempt reservations include unknown usage; they are not a provider dollar cap.
Live protocol/account acceptance remains unrun. See docs/META.md.

The expanded implementation still needs:

- Workspace membership and current authority on reads, actions and event streams.
- Revision checks when accepting results and immediately before permitted effects.
- Isolated, allowlisted tools and destinations, with bounded execution.
- Atomic spend reservations, bounded retries and visible unavailable usage.
- Stable destination idempotency or reconciliation after ambiguous failures.
- Evidence minimization and redaction, including downloaded reports.

Hosted model requests send selected inputs to the provider. Local storage does
not imply offline inference or zero retention. Provider terms and routing must
be explicit. This project makes no guarantee of universal malware prevention,
regulatory certification or error-free autonomous execution.

Until a private reporting channel is configured, do not publish exploit details
or sensitive information in an issue. Use GitHub's private vulnerability report
feature if enabled; otherwise contact the repository owner through an established
private channel.
