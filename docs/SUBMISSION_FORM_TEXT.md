# Relayloom: submission form, filled in (nothing has been submitted)

Copy each block into the form yourself. Items marked **YOU** need something only you have. Check the repository is public and the video opens in a private window before you press submit.
Deadline: 4 Nov 2026 9:00 PM ET (5 Nov 7:30 AM IST). Make no commits after you submit.

## Basics

| Field | Value |
| --- | --- |
| Project name | Relayloom |
| Track | Startups |
| Theme | Push the Frontier |
| Team | Solo: Sriharsan B S (bssriharsan@gmail.com) |
| Code repository | https://github.com/Sriharsan/relayloom (public, one author) |
| Live site | https://relayloom.vercel.app |
| Demo video | **YOU**: YouTube Unlisted link, 3 minutes or less |
| X post | **YOU**: link to your post (text in the last section) |
| Package | `python -m pip install relayloom` (PyPI only if you publish it, see the checklist) |
| Meta models used | Muse Glimmer 30B (Q4_K_M, llama.cpp), SAM 3.1 (Ultralytics). Both open weights, run locally. No paid API. |

## One line

Autonomous accounts payable that checks the goods, not just the paperwork.

## Short description (about 60 words)

A bill says 50 cartons. The dock got 46. Relayloom reads the bill with Muse Glimmer, counts what arrived in the dock photos with SAM 3.1, investigates any gap with cited evidence, and pays only what the books and the goods both support. It runs on Meta open weights on your own machine, keeps the owner in charge, and signs a receipt for every step.

## Problem (why it matters)

Companies pay bills for goods that never arrived, or arrived short. Paperwork matching (bill, order, receipt note) cannot see the dock. Real cases are in `docs/SOURCES.md`, each linked to its source: a supplier in New Jersey billed for goods never delivered for almost nine years (USD 9.5 million restitution, convicted); a federal office paid for eight units and got one (USD 20,720, substantiated); an Indian audit found Rs 7.20 crore paid for brush cutters not fully supplied. Allegations are labelled as allegations.

## What it does

1. **Reads the bill.** Muse Glimmer 30B turns the bill into a strict schema. Tax ids, bank accounts, phones and emails are masked first, and hidden text in a PDF never reaches the model.
2. **Counts what arrived.** SAM 3.1 counts goods in dock photos and video. The agent loop: Glimmer proposes up to four words, SAM is the counting tool, Glimmer looks at the overlay, and code owns the final number. A zero is a miss. A single count is accepted only if Glimmer's look agrees or a second word agrees. Otherwise the bill is held for a person.
3. **Investigates before a person sees it.** Recounts with a second wording, earlier deliveries, order price, last price, duplicate bills, supplier history. Every statement cites a record or photo and code checks each citation.
4. **Decides inside a policy the models cannot change.** Matching bills are entered and read back by a separate Checker. Mismatches, large bills, disputes and new bank details wait for the owner.
5. **Proves it.** Signed Ed25519 receipt chain verified in the browser and offline with `relayloom verify`.
6. **Works for the owner's language.** Phone alerts and the approval screen in English, Tamil and Hindi (135 strings). A Hindi and a Tamil bill were read by Muse Glimmer with every field correct.
7. **Offline.** Tested with the laptop disconnected, and in Docker on a network with no route out.

## Evidence (all from our own runs, see `docs/RESULTS.md`)

| Claim | Result |
| --- | --- |
| Demo benchmark, 30 deliveries built by us | Paperwork only caught 5 of 17 bad bills and let Rs 60,035.92 of wrong payments through. Paperwork plus goods caught 17 of 17, no wrong payment, no clean bill held. |
| Real purchase orders | 85 real orders from the State of California open data, 369 cases with documented exception types, all pass. Found and fixed real bugs (quantities above 100,000, fractional counts, multi-line orders, unit differences, concurrent receipt writes). |
| Package | 44 command line scenarios pass. A clean install with the network blocked passes 18 of 18 steps. 129 Python tests, plus browser tests. |
| Real photos | Free-licence stock plus the founder's own, counted by SAM 3.1 against hand counts. Total error was 33 items at the old setting and 12 at confidence 0.5, which is now the default. |
| Free GPU (Kaggle, two T4s) | Bill read 24 to 28 s warm, 88 s on the first call. SAM about 1 s per photo. Laptop CPU: 4.5 to 8.9 minutes. |
| Agent loop (Kaggle GPU) | 11 of 12 photos exactly right after the loop (5 of 12 on the first word), 1 held for a person, none wrong. On real photos with hand counts, 5 of 8 accepted within 3 items and 3 sent to a person. |

## Speed

On a free Kaggle GPU (two T4s) Muse Glimmer reads a bill in about 24 s once warm (88 s on the first call) and SAM 3.1 counts a photo in about 1 s, so a delivery is checked in under a minute. On a laptop CPU the same bill takes 4.5 to 8.9 minutes and runs as a background batch. Every control, match and policy step finishes in under a second. The dock detector reacts 0.25 s after the first movement.

## Theme fit: Push the Frontier

Open-weight vision and language models doing a job in the physical world of manufacturing and supply chains, locally, with an owner who stays in control. The model proposes and looks, code owns the count and the policy.

## How Meta models are used

- **Muse Glimmer 30B (Apache 2.0, GGUF Q4_K_M, llama.cpp):** reads bills to a strict JSON schema, proposes the words SAM should search for, looks at the SAM overlay image to judge the count, writes dispute drafts. Used on a laptop CPU and on a free Kaggle GPU.
- **SAM 3.1 (gated, access granted):** counts delivered goods from text prompts; tracks objects in video.
- No paid Meta API. Structured output and reasoning settings follow the official Meta open-weight cookbook.

## What was built during the hackathon

All of it, from 28 October 2026 (commit history in `docs/HACKATHON_UPDATES.md`). Three documentation commits from 26 October are labelled as before the building period. No code from an earlier private project was imported. One author.

## Scope

- Photos are real: free-licence stock and the founder's own. Bills and orders are a demo run, and 85 real California purchase orders drive 369 checked cases.
- Real cases come from courts, audits and news, each linked to its source. Allegations are labelled as allegations.
- Tamil and Hindi are approved by the founder.

## Run it

```
python -m pip install relayloom
relayloom doctor
relayloom check --bill-json bill.json --po po.json --counted 46
relayloom verify relayloom-out/receipts.jsonl
```

## X post (for the Most Viral prize)

The paperwork says 50. The dock got 46.

Relayloom is autonomous accounts payable that checks the goods, not just the paperwork. Meta's Muse Glimmer reads the bill, SAM 3.1 counts what arrived, and every step leaves a signed receipt anyone can verify.

Open weights. Runs on your own machine. English, Tamil, Hindi.

Tour: https://relayloom.vercel.app
Code: https://github.com/Sriharsan/relayloom

First reply: On 30 demo deliveries, paperwork alone caught 5 of 17 bad bills and paid Rs 60,035.92 wrongly. With the goods in the loop: 17 of 17 and nothing paid wrongly. Numbers are from our own runs, listed on the Proof page.

## Your steps before submitting

1. Hard refresh the live site (Ctrl+Shift+R) and look at Home and Proof.
2. Check the Tamil and Hindi strings in `docs/LANGUAGES.md`.
3. Record your voice over the picture, upload to YouTube as Unlisted.
4. Post on X with `docs/x/x-card.png` and the video; copy the post link.
5. Fill the form with this file. Submit yourself.
