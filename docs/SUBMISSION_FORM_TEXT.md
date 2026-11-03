# Text for the submission form and the X post

Paste-ready. Every figure comes from our own runs ([RESULTS.md](RESULTS.md), [BENCHMARK.md](BENCHMARK.md)). Check the
repository is public and the video link opens before you submit.

## Project name

Relayloom

## One line

Autonomous accounts payable that checks the goods, not just the paperwork.

## Short description (about 60 words)

A bill says 50 cartons. The dock got 46. Relayloom reads the bill with Muse Glimmer, counts what arrived in the dock
photos with SAM 3.1, investigates any gap with cited evidence, and pays only what the books and the goods both support.
It runs on a laptop CPU on Meta open weights, keeps the owner in charge, and signs a receipt for every step.

## Description

Relayloom is for the receiving and accounts payable team of a manufacturer or distributor that buys physical goods.

1. **Reads the bill.** Muse Glimmer 30B turns a bill into a strict schema. Tax ids, bank accounts, phones and emails are
   masked first, and text hidden in the PDF never reaches the model.
2. **Looks at what arrived.** SAM 3.1 counts the goods in every dock photo. A repeated photo is counted once, and several
   deliveries on one order add up as a running total.
3. **Investigates before a person sees it.** The Investigator recounts with a second wording, checks earlier deliveries, the
   order price, the last price paid, duplicate bills and the supplier's past shortfalls. Every statement cites a record or a
   photo, and code checks each citation and number before the finding is shown. It then names the likely cause and how sure the
   records let it be, and "unclear" is a valid answer.
4. **Decides within a policy the models cannot change.** Matching bills are entered and read back by a separate Checker.
   Mismatches, large bills, disputes and new bank details wait for the owner.
5. **Keeps a file and proves it.** Each case ends with a filed case file, and every step writes a signed receipt. The site verifies all of them in the browser and breaks the chain if one
   decision is changed.

On a synthetic set of 30 deliveries built by us, paperwork only caught 5 of 17 bad bills and let Rs 60,035.92 of wrong
payments through. Paperwork plus goods caught 17 of 17, made no wrong payment and held no clean bill.

Alerts reach the owner's phone over the local network with no internet, and every security control from input to boundary
passes its check and adds about 85 ms to a case.

## Theme

Push the Frontier: Meta's models meet the real world of physical goods, in manufacturing and supply chains. It also fits
Build for Your World for the team that lives this problem.

## How Meta models are used

- **Muse Glimmer 30B (open weights, Q4_K_M, llama.cpp):** reads bills with a strict JSON schema and writes dispute
  drafts. Runs on a laptop CPU with no GPU and no paid API. Nine Northgate bill readings are recorded with their timings
  (4 min 33 s to 8 min 51 s each, all valid).
- **SAM 3.1 (open weights, gated, access granted):** counts delivered goods from text prompts. 115 runs are saved, and the
  Investigator uses a second wording as an independent recount.
- No paid Meta API is used. The Reader follows the official Meta open-weight cookbook recipes for structured output and
  reasoning effort.

## What was built during the hackathon

All of it, from 28 October: the first workroom (28 to 30 October), then the accounts payable system from 31 October
(policy levels, masking, the agents, the Investigator, the receipts, the benchmark, the site). Every commit is listed in
[HACKATHON_UPDATES.md](HACKATHON_UPDATES.md). Three documentation commits from 26 October are labelled as before the
building period. No code from any earlier private project was imported.

## Links

- Code: https://github.com/Sriharsan/relayloom
- Live site with the guided demo and the receipt verifier: https://relayloom.vercel.app
- Video: add the link here

## Honest limits

Bills and photos are synthetic. On a CPU, Muse Glimmer needs about about 4 to 8 minutes per bill and SAM 3.1 about 41 seconds
per photo, so bills run as a background batch. Video counting is planned, not built.

## X post (for the Most Viral prize)

The paperwork says 50. The dock got 46.

Relayloom is accounts payable that checks the goods, not just the paperwork. Muse Glimmer reads the bill, SAM 3.1 counts what
arrived, an Investigator cites every claim, and signed receipts verify in your browser. All on Meta open weights, on a laptop.

Try the 60 second tour: https://relayloom.vercel.app

Add the video to the post, then paste the post link into the submission form. Engagement counts until 8 November end of day.
