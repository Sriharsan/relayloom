# Relayloom

**Relayloom: autonomous accounts payable that checks the goods, not just the paperwork.**

Agents read the bill, look at what actually arrived, investigate any gap with evidence, and pay only what
the books and the goods both support. Runs inside the company's own network on Meta open weight models.

The paperwork says 50. The dock got 46. Relayloom is for the receiving and accounts payable team of a
manufacturer or distributor that buys physical goods. The example company in this repository is
Northgate Components, with fictional suppliers and demo records only.

**Live site and proof:** https://relayloom.vercel.app. On a demo set of 30 deliveries built by us, paperwork only caught
5 of 17 bad bills and paperwork plus goods caught 17 of 17 with no wrong payment ([docs/BENCHMARK.md](docs/BENCHMARK.md)).

## Install the command line

```sh
python -m pip install relayloom                                         # from PyPI: https://pypi.org/project/relayloom/
relayloom doctor                                                         # what is ready on this machine, and the command that fixes the rest
relayloom check --bill-json bill.json --po po.json --counted 46          # no models needed: HELD or clear, with signed receipts
relayloom check --bill bill.pdf --photos dock/ --po po.json --agent      # Muse Glimmer proposes the words, SAM 3.1 counts, Glimmer looks at the overlay
relayloom verify relayloom-out/receipts.jsonl                            # verify the receipts offline
relayloom receipt relayloom-out/receipts.jsonl                           # a plain language PDF receipt, made offline
```

```sh
pip install -r requirements-ap.txt
python -m pytest -q                                   # 127 tests
python -m relayloom.ap.benchmark --counter recorded   # the benchmark on saved SAM 3.1 counts, a few seconds
python scripts/export_bench_run.py out.json           # the seven cases on the real agents, with signed receipts
python -m relayloom.ap --batch                        # the app on http://127.0.0.1:8800 (replays the saved readings)
python -m relayloom.ap --batch --phone                # also prints a link for alerts on a phone on the same Wi-Fi
python scripts/security_report.py                     # runs and times every security control
python scripts/record_demo_video.py                    # records the captioned picture of the live site to speak over
python scripts/add_voice.py my-voice.m4a              # puts your own voice on that picture and checks the three minute limit
python scripts/video_demo.py                          # a dock clip becomes a held delivery, from saved frames and counts
```

Recorded mode replays outputs from real runs on one laptop with their date, route and timings on screen, and uses a small
built in ledger. `--live` runs the models on your own machine and uses ERPNext (see below).

## What it does

1. **Reads the bill.** Muse Glimmer 30B turns a bill into a strict schema. Private numbers (GSTIN, bank account,
   IFSC, phone, email) are masked first. Text hidden in the PDF is found and never reaches the model.
2. **Looks at what arrived.** SAM 3.1 counts the goods in every photo of every delivery. Repeated photos are counted once.
   A purchase order can have several receiving events, and they add up as a running total.
3. **Matches.** Code compares order, bill and goods received, with tolerances from a policy file the model cannot change.
4. **Investigates every mismatch before a person sees it.** The Investigator recounts from every photo, adds up all deliveries
   on the order, checks the order price and the last price paid, looks for a duplicate bill, and checks the supplier's
   past shortfalls. Every statement in its finding cites a record, a photo or a recount, and code checks every citation
   and every number before the finding is shown. It then names the likely cause (short delivery, price above the order, duplicate bill,
   or the two counts disagree, or unclear), how sure the records let it be, and what to do next, and it proposes an action. The policy decides.
5. **Enters and checks.** A matching bill is entered by the Clerk, and a separate Checker reads it back and compares every
   field. Only then does the case say "entered and checked". Payment details only ever come from the supplier master.
6. **Waits for the owner where it matters.** Disputes, mismatches, bills above the owner's limit and new suppliers wait in
   the approval inbox. Muse Glimmer drafts the dispute and a browser agent files it in a local supplier portal.
7. **Keeps a file.** When a case ends, the Archivist writes a case file (cause, reasons, decision, the supplier's record) and puts its hash in
   the receipts. Later investigations of that supplier read the supplier file.
8. **Proves it.** Every step writes a signed receipt, chained per case, that anyone can verify offline. The audit trail is tamper-evident:
   change any recorded decision and the chain breaks at that step.

## Autonomy

Levels live in [`relayloom/ap/policy.json`](relayloom/ap/policy.json), read once at start. Bills, photos, model output
and requests cannot change them.

- **Runs alone:** read bills, count goods, match, investigate mismatches, enter matching bills, check the readback, reconcile after reconnect.
- **Waits for the owner:** any mismatch, any bill above the owner's amount limit, sending a dispute, a new supplier or changed bank details.
- **Never:** change bank details from invoice text, enter a bill whose readback failed, change the books while offline.

## What is real and what is labelled

| Part | Status |
| --- | --- |
| Muse Glimmer 30B reading bills and writing disputes | Real runs on a laptop CPU: 9 Northgate bill readings, all valid, 4 min 33 s to 8 min 51 s each, and 2 dispute drafts, plus 7 readings on the first bill set ([docs/RESULTS.md](docs/RESULTS.md)). Findings in recorded mode are written by code from the evidence. |
| SAM 3.1 counting photos | Real runs on the same CPU, 115 saved in `fixtures/recorded/sam` with the numbered overlays. 101 of the 102 counts the system uses match the delivery record. |
| ERPNext ledger | Real, in Docker on localhost. A built in ledger with the same calls is used in recorded mode. Each run says which ran. |
| Benchmark | Demo set built by us, real SAM 3.1 counts. See [docs/BENCHMARK.md](docs/BENCHMARK.md). In it the bills come from the generator and the findings are written by code. |
| Network boundary | **Tested in Docker on 3 November 2026, all checks pass** ([docs/boundary-result.json](docs/boundary-result.json)): the agents run on a network with no route out, direct connections fail, the gateway refuses hosts that are not in the policy and logs each refusal, and all seven cases pass inside. Verification with the laptop itself switched offline is one command, `python scripts/offline_check.py`, which writes a dated report. |
| Phone alerts | Built: `python -m relayloom.ap --phone`. A separate read only page on your local network, behind a random token, no internet. Covered by unit tests and verified end to end in a phone sized browser. |
| Security controls | 11 of 11 pass their checks and add about 30 ms to a case ([docs/SECURITY_CHECKS.md](docs/SECURITY_CHECKS.md)). |
| Video evidence | Built: `python scripts/dock_watch.py clip.mp4` (or a camera number or stream address). A delivery is detected 0.25 s after the first movement at 0.35 ms of compute per frame, the steady views become photographs, and SAM 3.1 counts them. Verified on a recorded demo clip (28 and 18 counted, 46 of 50 billed). The clip is demo. |
| Photos | Real photos, free-licence stock and the builder's own. 18 photos counted by SAM 3.1 with two words each, 8 with hand counts: at the old setting the total error was 33 items and at 0.5 it was 12 ([docs/REAL_GOODS.md](docs/REAL_GOODS.md), [docs/CONFIDENCE.md](docs/CONFIDENCE.md)). The default confidence is 0.5 because of this. |
| Real orders | 85 real purchase orders from the State of California open data, 369 cases with the exception types published accounts payable sources describe, all pass ([docs/REAL_WORLD_CHECK.md](docs/REAL_WORLD_CHECK.md)). Running it found and fixed real problems: quantities above 100,000, fractional counts, multi-line orders, unit of measure differences, concurrent receipt writes. |
| Package | `relayloom` 0.4.0 builds, passes the PyPI check, and installs and runs in a clean environment with the network blocked, 18 of 18 steps ([docs/PACKAGE_CHECK.md](docs/PACKAGE_CHECK.md)), plus 44 command line scenarios ([docs/PACKAGE_SCENARIOS.md](docs/PACKAGE_SCENARIOS.md)). |
| Languages | Phone alerts and the approval screen in English, Tamil and Hindi, 135 strings, every one listed in [docs/LANGUAGES.md](docs/LANGUAGES.md). A Hindi and a Tamil bill were read by Muse Glimmer with every field correct ([docs/LANGUAGE_BILL_RESULT.md](docs/LANGUAGE_BILL_RESULT.md)). |
| Real cases | Real cases from courts, audits and news, each linked to its source ([docs/SOURCES.md](docs/SOURCES.md)). |
| Sensors | Photos and camera video in, every item counted by SAM 3.1. |

Timings on the screen are real. On this laptop Muse Glimmer needs several minutes per bill and SAM 3.1 about a minute
per photo. That is why the app runs bills as a background batch.

## Run the cases

Each case is one command that prints PASS or FAIL per check and says which models and which ledger ran. They read bills from
the saved Muse Glimmer readings and count from the saved SAM 3.1 runs, so all seven pass from a clean clone in seconds.
`python scripts/export_bench_run.py out.json` runs them with signed receipts. To record fresh readings, run
`python scripts/record_glimmer.py` (about 1 hour on a laptop CPU).

```sh
python -m relayloom.ap.cases match       # a matching delivery, entered and checked, no person involved
python -m relayloom.ap.cases short       # paperwork says 50, the dock got 46: investigation, approval, dispute
python -m relayloom.ap.cases price       # rate above the order
python -m relayloom.ap.cases injection   # hidden text asking to change the bank account
python -m relayloom.ap.cases netcut      # network cut mid batch, reconnect, no duplicate
python -m relayloom.ap.cases duplicate   # same goods billed again under a new number
python -m relayloom.ap.cases split       # one order, two deliveries, one bill
python -m relayloom.ap.benchmark         # the benchmark on the demo set
```

Add `--live` to run Muse Glimmer and SAM 3.1 on your machine and the ledger in ERPNext.

## Running it live

1. **Muse Glimmer:** download `Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf` from `meta-models/Muse-Glimmer-30B-GGUF` and serve it with
   llama.cpp b10353 or newer (`llama-server --jinja`). Put its address in `.env` as `GLIMMER_URL`.
2. **SAM 3.1:** the weights are gated on Hugging Face. Request access, put a read token in `.env` as `HF_TOKEN`, and run
   `python scripts/record_sam.py`. It needs Ultralytics 8.4 or newer in the Python named by `RELAYLOOM_SAM_PYTHON`.
3. **ERPNext:** `docker compose -f pwd.yml up -d` from `frappe/frappe_docker`, then `python scripts/setup_erpnext.py`.
   It replaces the default password, creates an API user and seeds the demo records.

Keys live only in `.env`, which git ignores. The paid Meta Model API adapter in `relayloom/meta.py` is kept and stays off.

## Tests

```sh
python -m pytest -q                                   # 127 Python tests
node --test tests/ui.test.cjs tests/verify.test.cjs   # 14 Node tests
```

The site is built from `site-src` (`npm install`, `npm run data`, `npm run build`) into `site/`.

## Repository map

| Where | What |
| --- | --- |
| `relayloom/ap/` | The product: policy, masking, schema, matcher, Investigator, ledger, receipts, gateway, agents. |
| `fixtures/` | Demo bills, delivery photos and the benchmark set, plus `fixtures/recorded/` with real SAM 3.1 and Muse Glimmer outputs. |
| `docs/RESULTS.md`, `docs/BENCHMARK.md` | The evidence: timings, counts, the seven cases and the benchmark. |
| `site-src/` and `site/` | The website: source and the built version served on Vercel. |
| `scripts/` | Recording, exporting, fixtures and the boundary probe. |
| `deploy/` | The Docker network with no route out. |
| `relayloom/` (controller, server) and `web/` | The first workroom from 28 to 30 October. The accounts payable system reuses its approval, limit and receipt ideas. |

Built on Meta open weights and the official open-weight cookbook: the Reader uses the structured output and reasoning
effort recipes for Muse Glimmer ([sources](docs/SOURCES.md)). Theme: Push the Frontier.

## Hackathon

Meta Global AI Developer Hackathon, Startups track. The building period is 27 October to 4 November 2026 (ET).
Everything in this repository was built inside it; see [docs/HACKATHON_UPDATES.md](docs/HACKATHON_UPDATES.md) for each
commit and what it added. The shared revision workroom from 28 to 30 October is still here (`python -m relayloom`); the
accounts payable system is built on its approval, limit and receipt ideas.

## Read more

- [Benchmark](docs/BENCHMARK.md) · [Results from our own runs](docs/RESULTS.md) · [Sources](docs/SOURCES.md) · [Submission text](docs/SUBMISSION_FORM_TEXT.md)
- [Hackathon updates by commit](docs/HACKATHON_UPDATES.md) · [Submission notes](SUBMISSION_META.md) · [Video script](docs/VIDEO_SCRIPT.md)
- [Submission checklist](docs/SUBMIT_CHECKLIST.md) · [X post](docs/X_POST.md) · [Autonomy](docs/AUTONOMY.md) · [Product and architecture](docs/PRODUCT.md) · [Security](SECURITY.md)

Use demo information only. This is a loopback app, not a hosting service; do not expose its port.

## License and authorship

MIT. Original work by Sriharsan B S. No customers, pilots, revenue or funding are claimed.
