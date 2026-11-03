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

9 Northgate Components bill readings, each the text layer of a synthetic PDF bill, masked first, then read into the strict
schema. All 9 passed the schema check. Median 5 min 26 s per bill, fastest
4 min 33 s, slowest 8 min 51 s. End to end that is 0.7 to 1.3 output tokens per second, with prompts of
365 to 418 tokens. Recorded on 3 November 2026 with `python scripts/record_glimmer.py`.

| Bill | Recorded | Prompt tokens | Output tokens | Time | Schema |
| --- | --- | --- | --- | --- | --- |
| ARD-5101 | 2026-11-03 15:48 | 370 | 292 | 7 min 11 s | valid |
| CAL-0990 | 2026-11-03 15:57 | 366 | 421 | 8 min 51 s | valid |
| BRI-0731 | 2026-11-03 16:04 | 375 | 366 | 7 min 11 s | valid |
| ARD-5104 | 2026-11-03 16:09 | 418 | 332 | 5 min 20 s | valid |
| DUN-0211 | 2026-11-03 16:15 | 370 | 386 | 5 min 44 s | valid |
| BRI-0735 | 2026-11-03 16:20 | 375 | 404 | 5 min 16 s | valid |
| CAL-0992 | 2026-11-03 16:25 | 365 | 342 | 4 min 33 s | valid |
| DUN-0219 | 2026-11-03 16:30 | 370 | 328 | 5 min 26 s | valid |
| CAL-0994 | 2026-11-03 16:36 | 366 | 340 | 5 min 14 s | valid |

Muse Glimmer also wrote 2 dispute drafts for held deliveries, from the case facts:

| Case | Recorded | Prompt tokens | Output tokens | Time |
| --- | --- | --- | --- | --- |
| BRI-0731 | 2026-11-03 16:50 | 253 | 388 | 6 min 54 s |
| CAL-0990 | 2026-11-03 16:43 | 240 | 445 | 7 min 30 s |

Earlier, on 31 October, it read 7 bills of the first synthetic bill set, all valid, 4 min 56 s to
11 min 50 s each. In the recorded run, findings are written by code from the evidence, with every
citation checked. A model-written finding is wired in for live runs and was not recorded.

For comparison, Meta's open-weight cookbook lists Intel Core Ultra laptops as verified for Q4_K_M but gives no speed numbers for them yet.
These are ours, from a Core Ultra 7 155U on the CPU alone.

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
evidence, so Muse Glimmer's 4 min 33 s to 8 min 51 s per bill does not apply to those numbers.

## Network boundary in Docker (3 November 2026)

`docker compose -f deploy/boundary.compose.yml up --build` puts the agents on a network marked internal, so it has no route out, and
puts a gateway on both networks. Seven checks, all passed ([boundary-result.json](boundary-result.json)):

- Direct connections to 1.1.1.1 and 8.8.8.8 fail with "Network is unreachable", and the name example.com does not resolve.
- The gateway answers 403 to example.com and huggingface.co, which are not in the policy, and writes both refusals to its log.
- The seven cases run inside the container with the built in ledger and pass.

This is a network isolated test. It is not a run with the laptop itself switched offline.

## Not yet run

- A run with the laptop physically offline: `python scripts/offline_check.py` waits for Wi-Fi to go off, proves there is no network, then
  runs a live Muse Glimmer reading, a live SAM 3.1 count and all seven cases, and writes `docs/OFFLINE_RUN.md`. Until it has run, this
  repository says "network isolated" and never "air gapped".
- Muse Glimmer written findings. Findings are written by code in the recorded run.
- Video counting with SAM 3.1. Photos only.
