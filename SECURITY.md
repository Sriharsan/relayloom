# Security and privacy boundaries

This repository currently contains a planning scaffold, not a production service.
Do not put personal records, passwords, API keys or production data in issues,
commits, screenshots or demonstrations. Demonstration inputs must be synthetic.

The intended implementation must enforce:

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
