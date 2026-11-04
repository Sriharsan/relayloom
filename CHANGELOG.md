# Changelog

## 0.4.0

- `relayloom receipt receipts.jsonl`: a plain language PDF receipt made offline, with a line saying whether every signature and link checked out.
- Damaged goods: `check --damaged N`, or `check --agent --condition` where Muse Glimmer looks at each photo for dented, crushed or torn goods. Damaged units do not count as received, the bill is held, and the reason is written in plain words.
- The agent looks at the overlay as soon as one word has found something, so a single honest count is confirmed before the word budget runs out.
- Tamil and Hindi for the phone alerts and the approval screen.

## 0.3.0

- `relayloom check`, `verify`, `doctor`, `serve` and `models pull / serve` from one command.
- `check --agent`: Muse Glimmer proposes the words, calls SAM 3.1 as a tool, and looks at the numbered overlay itself. Code owns the number.
- `check --counted N` and `--json` for scripts and for running with no models at all.
- `doctor` says what is ready and the one command that fixes each missing piece, with no network calls beyond 127.0.0.1.
- Phone alerts with a QR code and photo upload over the local network.
- Signed receipts verified offline with `relayloom verify`.
