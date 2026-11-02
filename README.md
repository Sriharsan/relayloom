# Relayloom

**Relayloom: autonomous accounts payable that checks the goods, not just the paperwork.**

Agents read the bill, look at what actually arrived, investigate any gap with evidence, and pay only what
the books and the goods both support. Runs inside the company's own network on Meta open weight models.

The paperwork says 50. The dock got 46. Relayloom is for the receiving and accounts payable team of a
manufacturer or distributor that buys physical goods. The example company in this repository is
Northgate Components, with fictional suppliers and synthetic records only.

**Live site and proof:** https://relayloom.vercel.app. On a synthetic set of 30 deliveries built by us, paperwork only caught
5 of 17 bad bills and paperwork plus goods caught 17 of 17 with no wrong payment ([docs/BENCHMARK.md](docs/BENCHMARK.md)).

```sh
pip install -r requirements-ap.txt
python -m pytest -q                                   # 68 tests
python -m relayloom.ap.benchmark --counter recorded   # the benchmark on saved SAM 3.1 counts, a few seconds
python scripts/export_bench_run.py out.json           # the seven cases on the real agents, with signed receipts
python -m relayloom.ap --batch                        # the app on http://127.0.0.1:8800 (needs saved Muse Glimmer readings)
```

Rehearsal mode replays outputs from real runs on one laptop with their date, route and timings on screen, and uses a small
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
   and every number before the finding is shown. It proposes an action and the policy decides.
5. **Enters and checks.** A matching bill is entered by the Clerk, and a separate Checker reads it back and compares every
   field. Only then does the case say "entered and checked". Payment details only ever come from the supplier master.
6. **Waits for the owner where it matters.** Disputes, mismatches, bills above the owner's limit and new suppliers wait in
   the approval inbox. Muse Glimmer drafts the dispute and a browser agent files it in a local supplier portal.
7. **Proves it.** Every step writes a signed receipt, chained per case, that anyone can verify offline.

## Autonomy

Levels live in [`relayloom/ap/policy.json`](relayloom/ap/policy.json), read once at start. Bills, photos, model output
and requests cannot change them.

- **Runs alone:** read bills, count goods, match, investigate mismatches, enter matching bills, check the readback, reconcile after reconnect.
- **Waits for the owner:** any mismatch, any bill above the owner's amount limit, sending a dispute, a new supplier or changed bank details.
- **Never:** change bank details from invoice text, enter a bill whose readback failed, change the books while offline.

## What is real and what is labelled

| Part | Status |
| --- | --- |
| Muse Glimmer 30B reading bills, writing findings and disputes | Real runs on a laptop CPU: 7 bill readings, all valid, 4 min 56 s to 11 min 50 s each ([docs/RESULTS.md](docs/RESULTS.md)). Readings of the Northgate bills are recorded with `python scripts/record_glimmer.py`. |
| SAM 3.1 counting photos | Real runs on the same CPU, 115 saved in `fixtures/recorded/sam` with the numbered overlays. 101 of the 102 counts the system uses match the delivery record. |
| ERPNext ledger | Real, in Docker on localhost. A built in ledger with the same calls is used for rehearsal. Each run says which ran. |
| Benchmark | Synthetic set built by us, real SAM 3.1 counts. See [docs/BENCHMARK.md](docs/BENCHMARK.md). In it the bills come from the generator and the findings are written by code. |
| Network boundary | A Docker network with no route out and one logging gateway are built, and the gateway tests pass. The run with no route out and the run with the network disconnected are not done yet ([docs/RESULTS.md](docs/RESULTS.md)). |
| Delivery video counting | Not built. Photos only. |
| Sensors | None. Nothing is simulated. |

Timings on the screen are real. On this laptop Muse Glimmer needs several minutes per bill and SAM 3.1 about a minute
per photo. That is why the app runs bills as a background batch.

## Run the cases

Each case is one command that prints PASS or FAIL per check and says which models and which ledger ran. They read bills from
saved Muse Glimmer readings, so record the Northgate readings once first (`python scripts/record_glimmer.py`, about 2 hours on
a laptop CPU). `python scripts/export_bench_run.py out.json` runs the seven cases right away, with bill values from the bill
record and counts from the saved SAM 3.1 runs.

```sh
python -m relayloom.ap.cases match       # a matching delivery, entered and checked, no person involved
python -m relayloom.ap.cases short       # paperwork says 50, the dock got 46: investigation, approval, dispute
python -m relayloom.ap.cases price       # rate above the order
python -m relayloom.ap.cases injection   # hidden text asking to change the bank account
python -m relayloom.ap.cases netcut      # network cut mid batch, reconnect, no duplicate
python -m relayloom.ap.cases duplicate   # same goods billed again under a new number
python -m relayloom.ap.cases split       # one order, two deliveries, one bill
python -m relayloom.ap.benchmark         # the benchmark on the synthetic set
```

Add `--live` to run Muse Glimmer and SAM 3.1 on your machine and the ledger in ERPNext.

## Running it live

1. **Muse Glimmer:** download `Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf` from `meta-models/Muse-Glimmer-30B-GGUF` and serve it with
   llama.cpp b10353 or newer (`llama-server --jinja`). Put its address in `.env` as `GLIMMER_URL`.
2. **SAM 3.1:** the weights are gated on Hugging Face. Request access, put a read token in `.env` as `HF_TOKEN`, and run
   `python scripts/record_sam.py`. It needs Ultralytics 8.4 or newer in the Python named by `RELAYLOOM_SAM_PYTHON`.
3. **ERPNext:** `docker compose -f pwd.yml up -d` from `frappe/frappe_docker`, then `python scripts/setup_erpnext.py`.
   It replaces the default password, creates an API user and seeds the synthetic records.

Keys live only in `.env`, which git ignores. The paid Meta Model API adapter in `relayloom/meta.py` is kept and stays off.

## Tests

```sh
python -m pytest -q                                   # 68 Python tests
node --test tests/ui.test.cjs tests/verify.test.cjs   # 14 Node tests
```

The site is built from `site-src` (`npm install`, `npm run data`, `npm run build`) into `site/`.

## Hackathon

Meta Global AI Developer Hackathon, Startup track. The building period is 27 October to 4 November 2026 (ET).
Everything in this repository was built inside it; see [docs/HACKATHON_UPDATES.md](docs/HACKATHON_UPDATES.md) for each
commit and what it added. The shared revision workroom from 28 to 30 October is still here (`python -m relayloom`); the
accounts payable system is built on its approval, limit and receipt ideas.

## Read more

- [Benchmark](docs/BENCHMARK.md) · [Results from our own runs](docs/RESULTS.md) · [Sources](docs/SOURCES.md)
- [Hackathon updates by commit](docs/HACKATHON_UPDATES.md) · [Submission notes](SUBMISSION_META.md) · [Video script](docs/VIDEO_SCRIPT.md)
- [Autonomy](docs/AUTONOMY.md) · [Product and architecture](docs/PRODUCT.md) · [Security](SECURITY.md)

Use synthetic information only. This is a loopback app, not a hosting service; do not expose its port.

## License and authorship

MIT. Original work by Sriharsan B S. No customers, pilots, revenue or funding are claimed.
