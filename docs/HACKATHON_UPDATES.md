# Hackathon updates

Built from `git log` only. Times are the commit times recorded by git,
converted to US Eastern (EDT, UTC-04:00) from India Standard Time. Sriharsan B S is the only author of every commit.

## Event dates and where each commit falls

From the official participant guide (read 30 October, signed in):
the kickoff was Monday 26 October 2026, 12:00 PM ET, and the **building period
is 27 October to 4 November (ET)**. Submissions are due 4 November, 9:00 PM ET.

- `ec6dc51`, `4c13989` and `c6ea062` were committed on **26 October, 2:35 to
  2:46 PM ET** (27 October, 00:05 to 00:16 IST). That is after the kickoff but
  **before the building period**. They contain scope and planning documents only,
  no code. They are not presented as building period work.
- `3668d31`, 28 October, 9:08 AM ET, is the **first code commit** and is inside
  the building period. Every later commit is inside it too.
- Planning notes from 26 October informed the first documents. Those notes are
  not in this repository. A private prototype by the same founder exists; no
  private source, history, tests or data were imported (see
  [HACKATHON_PROVENANCE.md](HACKATHON_PROVENANCE.md)).

## Commits

| Commit | Date (ET) | What it added | Building period |
| --- | --- | --- | --- |
| `ec6dc51` | 26 Oct 2:35 PM | Project scope, contribution record, security notes, build and demo plans. Documents only, no runnable code. | Before (after kickoff). Documents only, adapted from 26 Oct planning. |
| `4c13989` | 26 Oct 2:36 PM | Product direction for connected operations and governed improvement. Documents only. | Before (after kickoff). Documents only. |
| `c6ea062` | 26 Oct 2:46 PM | Credit terms and submission guidance notes. Documents only. | Before (after kickoff). Documents only. |
| `3668d31` | 28 Oct 9:08 AM | The runnable product in one commit: SQLite revision controller, loopback HTTP server with sessions, CSRF and invites, parallel specialists with dependency waiting, selective reuse, stale output rejection, checked publication, the first web workroom, optional Meta adapter with a durable attempt ledger, 27 Python and 9 UI tests, CI workflow, MIT license. | Inside. First code. Work from 27 and 28 Oct committed together. |
| `e4654fa` | 30 Oct 8:32 AM | README opens with what Relayloom does and the single run command. | Inside |
| `c7b127c` | 30 Oct 11:59 AM | Meta mode names missing environment variables without echoing any value; the worker's text form hides the key. | Inside |
| `3c4814d` | 30 Oct 11:59 AM | `scripts/check_meta.*`: live Meta check that refuses unless `--i-have-credit` is passed, plus 7 offline tests with fake transports. | Inside |
| `ca0340c` | 30 Oct 11:59 AM | `.gitattributes` keeps shell scripts executable with LF endings. | Inside |
| `18f2ff6` | 30 Oct 12:01 PM | `scripts/check_demo.*`: rehearsal flow check over real local HTTP, PASS or FAIL per step. | Inside |
| `c5e3ff3` | 30 Oct 12:01 PM | `demo.ps1` and `demo.sh` launchers. | Inside |
| `c0408d5` | 30 Oct 12:08 PM | Autonomy policy file, recorded publish approvals, per revision run limits with escalation, outcome check after publication (VERIFIED, FAILED or UNKNOWN), 8 tests. | Inside |
| `469dfeb` | 30 Oct 12:09 PM | Demo check covers the approval record, verified outcome and fixed limits. | Inside |
| `c33d876` | 30 Oct 12:14 PM | Workroom redesign: dark control room, the revision loom, autonomy policy panel, approval and proof steps, 3 more UI tests. | Inside |
| `a98e2e4` | 30 Oct 12:14 PM | PowerShell launcher stops its Python child on exit. | Inside |

Commits after `a98e2e4` on 30 October add screenshots and documentation only
(this file, the video kit, submission notes and the README). The release notes
for the tag list them.

## What has not happened

- No live Meta model call has been made from this repository.
- No customer, pilot, revenue or funding exists or is claimed.
- All demo records are invented. Rehearsal outputs are deterministic text
  produced by code, not by a model.
