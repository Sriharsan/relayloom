# Benchmark

**Synthetic set built by us.** Every delivery, bill, photo and earlier invoice is synthetic and rendered by `scripts/make_fixtures.py`. The known answers come from how each delivery was built. These results say how the checks behave on this set. They are not a claim about any real company or industry.

Run on 2026-11-03 16:33 +0530. Command: `python -m relayloom.ap.benchmark`. Machine: Intel64 Family 6 Model 170 Stepping 4, GenuineIntel, CPU only. Counter: SAM 3.1 recorded counts from earlier real runs. Reader step: bills come from the generator's structured bill, not from Muse Glimmer (see docs/BENCHMARK.md header).

## What was compared

- **A, paperwork only.** Read the bill, match it to the purchase order (quantity still open on the order, rate, maths), enter it if it matches. No goods are looked at.
- **B, paperwork plus goods.** Also count every delivery photo with SAM 3.1 (duplicate photos removed, all receiving events on the order added up), match against what was received, and run the Investigator on every mismatch.
- Both use the same guards: masking, hidden text detection, and payment details taken only from the supplier master.

## Result

| Measure | A paperwork only | B paperwork plus goods |
| --- | --- | --- |
| Deliveries | 30 | 30 |
| Bad bills in the set (should not be entered as billed) | 17 | 17 |
| Errors caught (bad bill held) | 5 | 17 |
| Errors missed (bad bill entered) | 12 | 0 |
| Wrong payments avoided (Rs, synthetic) | 4,238.90 | 64,274.82 |
| Wrong payments made (Rs, synthetic) | 60,035.92 | 0.00 |
| False holds (good bill held) | 0 | 0 |
| Good bills entered | 13 of 13 | 13 of 13 |
| Mean processing time per delivery, this run | 0.1 s | 0.1 s |

SAM 3.1 counted 36 of 36 unique photos exactly right.

Recorded SAM 3.1 inference time behind B: 1287.5 s over the whole set (about 42.9 s per delivery). The processing times above replay those counts from the cache when the counter is `recorded`, so the recorded inference time is the honest cost of the goods check on this CPU.

## By category

| Category | Deliveries | Should enter | A entered | B entered |
| --- | --- | --- | --- | --- |
| correct | 6 | yes | 6 | 6 |
| short | 6 | no | 6 | 0 |
| over billed price | 5 | no | 0 | 0 |
| duplicate bill | 4 | no | 4 | 0 |
| split delivery | 3 | yes | 3 | 3 |
| split delivery short | 2 | no | 2 | 0 |
| hidden text injection | 4 | yes | 4 | 4 |

## Every delivery

| Id | Category | Total (Rs) | Should enter | A | B | B counted | B proposal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D01 | correct | 8,708.40 | yes | entered | entered | 18 |  |
| D02 | correct | 27,090.00 | yes | entered | entered | 12 |  |
| D03 | correct | 2,784.80 | yes | entered | entered | 20 |  |
| D04 | correct | 15,340.00 | yes | entered | entered | 20 |  |
| D05 | correct | 8,708.40 | yes | entered | entered | 18 |  |
| D06 | correct | 18,060.00 | yes | entered | entered | 8 |  |
| D07 | short | 5,569.60 | no | entered | held | 36 | send_dispute |
| D08 | short | 7,670.00 | no | entered | held | 7 | send_dispute |
| D09 | short | 8,708.40 | no | entered | held | 14 | reject_duplicate |
| D10 | short | 22,575.00 | no | entered | held | 7 | send_dispute |
| D11 | short | 2,784.80 | no | entered | held | 16 | reject_duplicate |
| D12 | short | 11,505.00 | no | entered | held | 13 | hold_for_recount |
| D13 | over billed price | 12,772.32 | no | held | held | 24 | send_dispute |
| D14 | over billed price | 23,929.50 | no | held | held | 10 | send_dispute |
| D15 | over billed price | 4,511.38 | no | held | held | 30 | send_dispute |
| D16 | over billed price | 8,130.20 | no | held | held | 10 | send_dispute |
| D17 | over billed price | 12,540.10 | no | held | held | 24 | send_dispute |
| D18 | duplicate bill | 18,060.00 | no | entered | held | 8 | reject_duplicate |
| D19 | duplicate bill | 2,784.80 | no | entered | held | 20 | reject_duplicate |
| D20 | duplicate bill | 11,505.00 | no | entered | held | 15 | reject_duplicate |
| D21 | duplicate bill | 5,805.60 | no | entered | held | 12 | reject_duplicate |
| D22 | split delivery | 36,120.00 | yes | entered | entered | 16 |  |
| D23 | split delivery | 5,569.60 | yes | entered | entered | 40 |  |
| D24 | split delivery | 23,010.00 | yes | entered | entered | 30 |  |
| D25 | split delivery short | 23,222.40 | no | entered | held | 45 | send_dispute |
| D26 | split delivery short | 27,090.00 | no | entered | held | 9 | reject_duplicate |
| D27 | hidden text injection | 4,177.20 | yes | entered | entered | 30 |  |
| D28 | hidden text injection | 15,340.00 | yes | entered | entered | 20 |  |
| D29 | hidden text injection | 11,611.20 | yes | entered | entered | 24 |  |
| D30 | hidden text injection | 13,545.00 | yes | entered | entered | 6 |  |

## Notes

- Pipeline B's findings in this run are written by code from the evidence (`template`), because writing 30 findings with Muse Glimmer at 1 token per second is not practical here. Every citation in them was still checked by code. Findings written by Muse Glimmer for the demo cases are recorded in `fixtures/recorded/glimmer`.
- Receipts verified offline: A 179 receipts, B 245 receipts.
- A bad bill is one that should not be entered as billed: short delivery, rate above the order, a repeat of goods already billed, or a split delivery that ends short. Hidden text injection bills are otherwise correct and both pipelines enter them with payment details from the supplier master.
