# Hackathon updates

Built from `git log` only. Times are the commit times recorded by git, in India
Standard Time (UTC+05:30). Sriharsan B S is the only author of every commit.

## Event dates and the open question

- The Meta Global AI Developer Hackathon kicked off on 26 October 2026.
  Workshops ran from 27 October.
- The repository's first commit is 27 October 2026, 00:05 IST
  (26 October, 14:35 US Eastern), after the kickoff.
- **The eligible build start is not confirmed.** This file does not decide it.
  The column "Relative to kickoff" states only what git shows. Whether each
  commit counts as hackathon work depends on the organizer's rule.
- Planning notes from 26 October informed the first documents. Those notes are
  not in this repository. A private prototype by the same founder exists; no
  private source, history, tests or data were imported (see
  [HACKATHON_PROVENANCE.md](HACKATHON_PROVENANCE.md)).

## Commits

| Commit | Date (IST) | What it added | Relative to kickoff |
| --- | --- | --- | --- |
| `ec6dc51` | 27 Oct 00:05 | Project scope, contribution record, security notes, build and demo plans. Documents only, no runnable code. | After kickoff. Text adapted from 26 Oct planning. |
| `4c13989` | 27 Oct 00:06 | Product direction for connected operations and governed improvement. Documents only. | After kickoff |
| `c6ea062` | 27 Oct 00:16 | Credit terms and submission guidance notes. Documents only. | After kickoff |
| `3668d31` | 28 Oct 18:38 | The runnable product in one commit: SQLite revision controller, loopback HTTP server with sessions, CSRF and invites, parallel specialists with dependency waiting, selective reuse, stale output rejection, checked publication, the first web workroom, optional Meta adapter with a durable attempt ledger, 27 Python and 9 UI tests, CI workflow, MIT license. | After kickoff. Work from 27 and 28 Oct committed together. |
| `e4654fa` | 30 Oct 18:02 | README opens with what Relayloom does and the single run command. | After kickoff |
| `c7b127c` | 30 Oct 21:29 | Meta mode names missing environment variables without echoing any value; the worker's text form hides the key. | After kickoff |
| `3c4814d` | 30 Oct 21:29 | `scripts/check_meta.*`: live Meta check that refuses unless `--i-have-credit` is passed, plus 7 offline tests with fake transports. | After kickoff |
| `ca0340c` | 30 Oct 21:29 | `.gitattributes` keeps shell scripts executable with LF endings. | After kickoff |
| `18f2ff6` | 30 Oct 21:31 | `scripts/check_demo.*`: rehearsal flow check over real local HTTP, PASS or FAIL per step. | After kickoff |
| `c5e3ff3` | 30 Oct 21:31 | `demo.ps1` and `demo.sh` launchers. | After kickoff |
| `c0408d5` | 30 Oct 21:38 | Autonomy policy file, recorded publish approvals, per revision run limits with escalation, outcome check after publication (VERIFIED, FAILED or UNKNOWN), 8 tests. | After kickoff |
| `469dfeb` | 30 Oct 21:39 | Demo check covers the approval record, verified outcome and fixed limits. | After kickoff |
| `c33d876` | 30 Oct 21:44 | Workroom redesign: dark control room, the revision loom, autonomy policy panel, approval and proof steps, 3 more UI tests. | After kickoff |
| `a98e2e4` | 30 Oct 21:44 | PowerShell launcher stops its Python child on exit. | After kickoff |

Commits after `a98e2e4` on 30 October add screenshots and documentation only
(this file, the video kit, submission notes and the README). The release notes
for the tag list them.

## What has not happened

- No live Meta model call has been made from this repository.
- No customer, pilot, revenue or funding exists or is claimed.
- All demo records are invented. Rehearsal outputs are deterministic text
  produced by code, not by a model.
