# Hackathon contribution record

## Event and boundary

Meta Global AI Developer Hackathon, Startup track. Repository created on
27 October 2026, Asia/Kolkata. Git timestamps record the actual commit time.
The organizer's precise eligible-start interpretation remains to be confirmed;
this timestamp alone does not establish eligibility.

The founder previously worked on a private agent-operations prototype. Its
existing scheduler, review, recovery, security controls and interface are prior
work. They are not presented as newly built for the event. No private source,
history, tests, data or implementation has been imported in this initial commit.

Some planning and research began on 26 October. The public documents in this
commit are adapted from that planning. New repository dates do not reset the
age of those ideas or materials.

The intended new implementation is shared intent revision, dependency-aware
replanning, valid-work reuse and their live demonstration with Meta models.
Implementation status must be established by commits and tests, not this plan.

## Ledger

| Entry | Origin/date | Files | Evidence/status |
| --- | --- | --- | --- |
| Public project scaffold | Adapted from 26 October planning; published 27 October | README.md, AGENTS.md, SECURITY.md, docs/* | Documentation only; no runnable product |
| Shared intent revision | New public implementation, 28 October | relayloom/controller.py, relayloom/server.py, tests/test_controller.py | Transactional revisions, role and CSRF tests; final release commit recorded by parent |
| Live Meta-backed parallel acceptance | Pending separate approval/access | Optional adapter is implemented; live run not performed | No live API call claimed |
| Optional Meta transport and durable attempt ledger | New public implementation, 28 October | relayloom/meta.py, controller.py, __main__.py, tests/test_meta.py, docs/META.md | 11 offline tests including prompt/reuse field alignment; real inference disabled by default and unrun |
| Selective replanning and reuse | New public implementation, 28 October | relayloom/controller.py, tests/test_controller.py | Parallel/wait, selective reuse, late-output and checked publication tests; no savings claimed |
| Shared live interface and outcome proof | New public implementation, 27–28 October | web/*, relayloom/server.py | Browser consumes real state/SSE; synthetic outputs, no Meta inference claimed; final visual acceptance separate |
| Local rehearsal and public license | New public implementation, 28 October | relayloom/*, tests/*, LICENSE, docs/IMPLEMENTATION.md | 27 tests passed including offline Meta; MIT license for original source |
| Session-safe readable workroom | New public implementation, 28 October | web/*, tests/ui.test.cjs, .github/workflows/checks.yml | 9 UI state tests; local owner/editor browser rehearsal and checked publication; no live inference |

Add a row for each implemented change with its commit, date, exact paths,
verification and corresponding demo moment. Preserve failed and unrun checks.

## Reuse

Public documentation and repositories informed planning. No third-party code is
bundled in the initial scaffold. Any later dependency or copied material needs
its source, pinned version, license and required notices recorded here.

The demo must identify event-built functionality clearly. Do not expose private
commercial material simply to provide context; explain prior work in words.
