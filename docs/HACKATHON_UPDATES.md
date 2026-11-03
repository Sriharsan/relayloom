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
  not in this repository. A private earlier project by the same founder exists; no
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

Commits `ec15789` to `e7eb2bc` (30 and 31 October) add screenshots and documentation only: this file, the autonomy notes,
the video script, the submission notes and the README. Every commit below is inside the building period.

| Commit | Date (ET) | What it added |
| --- | --- | --- |
| `ca62000` | 31 Oct 1:46 PM | Accounts payable core: policy levels in a file the model cannot change, signed receipt chain, masking of tax ids, bank accounts, phones and emails, strict bill schema, three way match, ledger adapter. |
| `cc8ed60` | 31 Oct 1:46 PM | Demo suppliers, purchase orders, bill PDFs and rendered delivery photos (replaced by the Northgate Components set in `6597d87`). |
| `82a78c9` | 31 Oct 1:46 PM | Agents for read, count, match, enter, check and dispute, egress gateway, local supplier portal and tests. |
| `5b13b84` | 31 Oct 1:46 PM | First real Muse Glimmer 30B bill reading on this laptop's CPU. |
| `ed73145` | 31 Oct 1:47 PM | Fixture bytes kept exact so recorded model inputs hash the same on every clone. |
| `3356d7b` | 31 Oct 1:49 PM | Receipt verification in the browser with WebCrypto Ed25519, same canonical bytes as Python. |
| `ef16205` | 1 Nov 1:06 AM | Accounts payable app and UI, five case runner, boundary files and six more Muse Glimmer readings. |
| `1cad2f0` | 1 Nov 1:44 AM | Real SAM 3.1 counts for the delivery photos, ERPNext seeding fix. |
| `8024117` | 1 Nov 1:53 AM | Batch rows stack on narrow screens, screenshot script. |
| `6cf3440` | 1 Nov 1:00 AM EST | Sources list and site data builder. |
| `6597d87` | 1 Nov 1:17 AM EST | Northgate Components replaces the first story everywhere in code, fixtures and tests. Receiving log with duplicate photo detection, the Investigator with code-verified citations, running total matching across receiving events, multi photo counting. |
| `280b7e9` | 1 Nov 1:21 AM EST | Investigation panel and per photo gallery in the app, Benchmark page, benchmark runner. |
| `4670f87` | 1 Nov 1:23 AM EST | Requirements for the accounts payable app, CI installs them, screenshots of the earlier story removed. |
| `f8de996` | 2 Nov 11:24 AM EST | Site rebuilt from the Lovable design in `site-src`, reading every figure from exported run files. New recount wordings after trials: cylinder, package, spool. More real SAM 3.1 recordings. |
| `2a5ed30` | 2 Nov 11:56 AM EST | The 30 delivery benchmark on real SAM 3.1 counts, added to the Proof page. |
| `304c87c` | 2 Nov 12:00 PM EST | Every page route served from the app on Vercel. |
| `9b07b9b` | 2 Nov 12:25 PM EST | Docs updated to the measured results and the live site link; the offline verifier restored; "demo" used everywhere. |
| `16d54b8` | 3 Nov 5:29 AM EST | A guided tour on the Demo page, Five clicks to try it, and a set up section laid out like Meta's open-weight cookbook. |
| `f6c46c5` | 3 Nov 5:30 AM EST | Repository map in the README and paste-ready submission and X post text. |
| `a8072c8` | 3 Nov 5:37 AM EST | Track named "Startups", as in the guide. |
| `7211000` | 3 Nov 6:05 AM EST | The likely cause of a mismatch with its reasons, a case file for every finished case, and the supplier file. 4 tests. |
| `a38e479` | 3 Nov 6:26 AM EST | Alerts to a phone on the local network, the security cost report (11 controls), a balanced Case screen, and the Northgate Muse Glimmer recordings (9 readings, 2 disputes). |
| `6640b51` | 3 Nov 11:26 AM EST | The Docker boundary proof passes, the offline check script, and the evidence on the site. |
| `ee3023b` | 3 Nov 12:20 PM EST | Confident, official wording: a roadmap, a tamper-evident audit trail, entry and verification as separate duties. |
| `21586a7` | 3 Nov 3:15 PM EST | Video evidence: a dock detector, key frames counted by SAM 3.1, and the case from a video. |
| `6986992` | 3 Nov 10:26 AM EST | The landing page tells the story (who we are, why we matter, why you need us, with three primary sources), weak wording removed, share tags and the X card, and a clearer checks workflow. |
| `96b6351` | 3 Nov 10:40 AM EST | A Python 3.12 only f-string fixed so everything runs on Python 3.11, and CI compiles every file. |

The commit that adds this table also updates the README, submission notes, results and the wording of the demo data labels.

## Scope

- The paid Meta Model API adapter stays switched off. The project runs Meta open weights.
- Muse Glimmer 30B and SAM 3.1 open weights have run on this laptop. Numbers and timings are in [RESULTS.md](RESULTS.md).
- No customer, pilot, revenue or funding is claimed.
- All demo records are demo. The first workroom's rehearsal outputs are deterministic text produced by code, not by a model.
