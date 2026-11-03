# Relayloom: Meta Global AI Developer Hackathon submission notes

Startups track. Submissions due 4 November 2026, 9:00 PM US Eastern (5 November, 7:30 AM IST).
Author: Sriharsan B S, the only contributor.

**Relayloom: autonomous accounts payable that checks the goods, not just the paperwork.**
Agents read the bill, look at what actually arrived, investigate any gap with evidence, and pay only what the books and
the goods both support. Runs inside the company's own network on Meta open weight models.

## Theme, track and prizes

Source: the participant guide, read again on 3 November 2026.

- **Theme: Push the Frontier.** The guide names manufacturing and controlling a physical system. Relayloom puts Meta's models
  between paperwork and the real world: SAM 3.1 looks at the goods that arrived and Muse Glimmer reads the bill.
  It also fits Build for Your World, for the receiving and accounts payable team that lives this problem.
- **Track: Startups.** One project, one Representative (Sriharsan B S), and the only person who worked on it.
- **Judged on:** Impact 30%, Use of Meta AI Tooling 25%, Technical Depth and Execution 20%, Demo 25%.
- **Prizes flagged:** Best Build on Meta Open Weight Models (Muse Glimmer on this laptop's CPU, no paid API) and Best Agentic Use-Case
  (autonomy levels, investigation, approval, receipts). Most Viral Project: post the demo on X and submit the post link on the
  platform; engagement counts until 8 November end of day.
- **Deadline:** Wednesday 4 November, 9:00 PM Eastern (Thursday 5 November, 7:30 AM IST). Late submissions are not considered.
  Before submitting, check that the repository is public and the video link opens.

## Links

- Repository: https://github.com/Sriharsan/relayloom
- Live site (home, proof with a receipt verifier that runs in your browser, and a replay of the app): https://relayloom.vercel.app
- Video: linked from the live site and the submission form once uploaded.
- X post for the Most Viral prize: added to the submission form once posted. Script: [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)

## Use of Meta models (open weights, run on one laptop CPU)

| Model | Used for | Evidence |
| --- | --- | --- |
| Muse Glimmer 30B (Apache 2.0, Q4_K_M, llama.cpp) | Reads bills into a strict schema and writes dispute drafts | 9 Northgate bill readings, all valid against the schema, 4 min 33 s to 8 min 51 s each, plus 2 dispute drafts. [docs/RESULTS.md](docs/RESULTS.md) |
| SAM 3.1 (facebook/sam3.1, gated, access granted) | Counts delivered goods in every dock photo | 115 saved runs in `fixtures/recorded/sam`, 101 of the 102 counts used by the system match the delivery record, about 41 s per photo |

The paid Meta Model API adapter in `relayloom/meta.py` is kept and stays off. No paid route is used anywhere.

## What the entry shows

1. A bill says 50 cartons. SAM 3.1 counts 46 on the dock photos (a repeated photo is counted once).
2. The Investigator recounts, adds up earlier deliveries on the order, checks the price and the supplier's history, and writes a
   finding. Every statement cites a record, photo or recount, and code checks every citation and number first.
3. The Investigator names the likely cause (here, the supplier shipped less than it billed), how sure the records let it be,
   and what to do next. "Unclear" is a valid answer. Every reason cites a record.
4. The policy holds the bill for the owner. After approval a dispute is drafted and filed. Nothing is entered.
5. A dock video is detected within a quarter of a second, its steady views are counted by SAM 3.1, and the delivery enters the
   same investigation. Verified on a recorded demo clip; a camera stream uses the same reader.
6. Hidden text in a bill that asks to change the bank account is ignored and receipted.
7. A network cut mid batch holds the books. After reconnect nothing is entered twice.
8. A case file is written when each case ends, with the cause, the decision and the supplier's record. Its hash is in the receipts.
   Every step writes a signed receipt, chained per case. The Proof page verifies all 90 receipts of the demo run in the browser,
   and fails exactly one when a decision is changed.

Benchmark on a demo set built by us, 30 deliveries with known answers: paperwork only caught 5 of 17 bad bills and let
Rs 60,035.92 of wrong payments through; paperwork plus goods caught 17 of 17, made no wrong payment and held no clean bill.
Details and caveats: [docs/BENCHMARK.md](docs/BENCHMARK.md).

## What is real and what is labelled

- Measured: SAM 3.1 counts and times, Muse Glimmer readings and times, case outcomes, signed receipts, benchmark numbers.
- Labelled: bills, photos, companies, suppliers and money are demo. In the demo replay the bill values come from the bill
  record. Findings in the benchmark are written by code from the evidence.
- Built and tested: alerts to a phone on the local network (read only, token link, no internet) and 11 security controls that all
  pass and add about 30 ms to a case ([docs/SECURITY_CHECKS.md](docs/SECURITY_CHECKS.md)). The phone page was tested in a phone sized
  browser, not on a physical phone.
- Tested: the agents on a Docker network with no route out, where direct connections fail and the gateway refuses unlisted hosts
  and logs them, and all seven cases pass inside ([docs/boundary-result.json](docs/boundary-result.json)).
- Next verification: the run with the laptop itself switched offline (`python scripts/offline_check.py`, which writes a dated report).
  Findings are written by code from the evidence in the recorded run. See the end of [docs/RESULTS.md](docs/RESULTS.md).
- No customers, pilots, revenue or funding are claimed.

## Rules and timing

Source: the official participant guide, https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details (sign in needed),
read 30 October 2026. One project per team, public repository, a demo video of three minutes that shows what was built during
the hackathon. Building period: 27 October to 4 November (ET).

- Commits `ec6dc51`, `4c13989` and `c6ea062` (26 October, 2:35 to 2:46 PM ET) are scope documents made after kickoff and before
  the building period. The first code is `3668d31`, 28 October, 9:08 AM ET.
- The accounts payable system, the Northgate story, the Investigator, the benchmark and the site were all built from 31 October
  on. Each commit is listed in [docs/HACKATHON_UPDATES.md](docs/HACKATHON_UPDATES.md).
- The shared revision workroom from 28 to 30 October is still in the repository. The accounts payable system reuses its
  approval, limit and receipt ideas. A private earlier project by the same founder exists and no part of it was imported
  ([docs/HACKATHON_PROVENANCE.md](docs/HACKATHON_PROVENANCE.md)).

## How to run

```sh
pip install -r requirements-ap.txt
python -m pytest -q
python -m relayloom.ap.benchmark --counter recorded   # the benchmark on saved SAM 3.1 counts, a few seconds
python scripts/export_bench_run.py out.json           # the seven cases on the real agents, with signed receipts
```

The site is built from `site-src` (`npm install`, `npm run data`, `npm run build`) into `site/`.

## Left for the founder

- Record and upload the video, then add its link to the site (`links.video` in `site-src/src/data/site.ts`) and the submission form.
- Submit on the CV platform by 4 November, 9:00 PM ET.
