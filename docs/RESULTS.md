# Results from our own runs

Every number on this page comes from a run on the machine below, on synthetic records. The live site shows the same
figures: https://relayloom.vercel.app (the Proof page). Recorded outputs are in `fixtures/recorded/`, each with its date,
route, model and timings.

## The machine (checked 31 October 2026)

| Part | Value |
| --- | --- |
| Operating system | Windows 11 Home 10.0.26300 |
| CPU | Intel Core Ultra 7 155U, 12 cores, 14 threads |
| Memory | 31.4 GB |
| GPU | Intel integrated graphics, no NVIDIA GPU, so no `nvidia-smi` |
| Docker | Docker Desktop, engine 28.1.1 |
| Tesseract | Not installed. Masking works on the text layer of PDF bills. |

Route for Muse Glimmer: CPU on this laptop. There is no GPU with 24 GB. Muse Glimmer 30B Q4_K_M, llama.cpp b12020 CPU, this laptop, file
`Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf` from `meta-models/Muse-Glimmer-30B-GGUF` (Apache 2.0), served by
`llama-server --jinja -c 8192 -np 1 -t 10 --no-repack` with a reasoning budget of 1024 tokens.

## Muse Glimmer 30B reading bills

7 bill readings, each the text layer of a synthetic PDF bill, masked first, then read into the strict schema.
All 7 passed the schema check. Average 7 min 55 s per bill, fastest
4 min 56 s, slowest 11 min 50 s.

| Reading | Recorded | Prompt tokens | Output tokens | Time | Schema |
| --- | --- | --- | --- | --- | --- |
| Reading 1 | 2026-10-31 23:09 | 362 | 404 | 8 min 11 s | valid |
| Reading 2 | 2026-10-31 23:16 | 366 | 387 | 7 min 27 s | valid |
| Reading 3 | 2026-10-31 23:28 | 357 | 373 | 11 min 50 s | valid |
| Reading 4 | 2026-10-31 23:36 | 410 | 475 | 7 min 56 s | valid |
| Reading 5 | 2026-10-31 23:45 | 359 | 377 | 9 min 04 s | valid |
| Reading 6 | 2026-10-31 23:51 | 366 | 391 | 6 min 03 s | valid |
| Reading 7 | 2026-10-31 23:56 | 357 | 346 | 4 min 56 s | valid |

These readings were recorded on 31 October on the first synthetic bill set. The nine Northgate Components bills are read
with `python scripts/record_glimmer.py`, which saves each reading with its route and timings.

## SAM 3.1 counting delivered goods

102 counts with the two prompt wordings the system uses per item (the first count and the Investigator's independent
recount): **101 match the delivery record.** Average
41.3 s per photo on the CPU, fastest 22.9 s, slowest
109.9 s. The one miss: REC-B12-P1 with the wording 'spool' counted 3 against 13.
The Investigator treats a disagreement between the two counts as a reason to hold the bill for a person, and the
benchmark shows that hold as it happened.

The recount wording for each item was chosen from trials on the first demo photos. 13 trial runs with other
wordings are saved with the rest, and 8 of them returned 0:

| Photo | Wording | Counted | Delivery record |
| --- | --- | --- | --- |
| REC-H01-P1 | carton | 38 | 38 |
| REC-H03-P1 | container | 24 | 24 |
| REC-H04-P1 | cable reel | 0 | 20 |
| REC-H04-P1 | reel | 0 | 20 |
| REC-H05-P1 | bottle | 0 | 24 |
| REC-H05-P1 | canister | 0 | 24 |
| REC-H05-P1 | container | 0 | 24 |
| REC-H05-P1 | jug | 0 | 24 |
| REC-H05-P1 | tin | 0 | 24 |
| REC-H06-P1 | box | 28 | 28 |
| REC-H06-P1 | carton | 28 | 28 |
| REC-H06-P2 | box | 18 | 18 |
| REC-H06-P2 | carton | 0 | 18 |

Final wordings: cans "can" and "cylinder", cartons "cardboard box" and "package", sacks "sack" and "bag", cable reels "roll" and
"spool". The benchmark photos were not used to pick them.

## The seven cases (one run of the real agents)

`scripts/export_bench_run.py` runs the agents, matcher, Investigator, approval policy, built in ledger and Checker on the
demo bills and writes signed receipts. Bill values come from the bill record in this run, and counts come from the saved
SAM 3.1 runs. Each held case also gets a likely cause with its reasons (short delivery, price above the order, duplicate bill, or the two counts
disagree) and a case file whose hash is in the receipt chain. Result: matching delivery entered and checked; short delivery (50 billed, 46 received) held, approved by the
owner, dispute sent, nothing entered; price above the order rejected by the owner; hidden text ignored and the bill entered with
payment details from the supplier master; duplicate bill rejected; split delivery entered as a running total; network cut:
1 invoice in the books while cut and 3 after reconnect, none twice.

Receipts: 90 signed receipts over 9 cases, all verified (Ed25519 signature, SHA 256 hash and chain order). The Proof page
verifies them in your browser, and `python scripts/export_bench_run.py` regenerates the run and checks them offline.

## Benchmark (synthetic set built by us)

30 deliveries with known answers, two pipelines on the same set. Full tables in [BENCHMARK.md](BENCHMARK.md).

| Measure | Paperwork only | Paperwork plus goods |
| --- | --- | --- |
| Bad bills caught | 5 of 17 | 17 of 17 |
| Bad bills entered | 12 | 0 |
| Wrong payments made (Rs, synthetic) | 60,035.92 | 0.00 |
| Clean bills held by mistake | 0 of 13 | 0 of 13 |

SAM 3.1 counted 36 of 36 benchmark photos exactly right. The goods check costs about 42.9 s per delivery of
SAM 3.1 time on this CPU. In the benchmark the bills come from the generator and the findings are written by code from the
evidence, so Muse Glimmer's 4 min 56 s to 11 min 50 s per bill does not apply to those numbers.

## Not yet run

- The Docker network with no route out (`deploy/boundary.compose.yml`) and the run with the network physically
  disconnected. Until they run, this repository makes no network isolation claim beyond the gateway tests.
- Muse Glimmer readings of the nine Northgate bills, and Glimmer written findings and disputes for the demo cases.
- Video counting with SAM 3.1. Photos only.
