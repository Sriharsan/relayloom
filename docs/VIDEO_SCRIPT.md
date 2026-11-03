# Demo video script (3 minutes)

The video shows only work built from 27 October. **You speak it, in your own voice.** The demo should be felt and delivered by a human, so the
captioned video is only the picture. Do not upload it silent.

Two good ways to record:

1. **Voice over the picture.** Play `relayloom-demo-picture-only.mp4`, read the lines below as it plays, and record your voice with the Windows Voice
   Recorder or your phone. Then run `python scripts/add_voice.py your-voice.m4a`. It puts your voice on the picture and checks the three minute limit.
2. **Record yourself live.** Open https://relayloom.vercel.app, start Xbox Game Bar (Win+G) or OBS, and follow the same scenes while you speak.

Make it yours: add one sentence of your own before the hook, about why this problem matters to you. Speak calmly, one idea at a time, and pause where
a number appears on screen. The lines are a guide, so say them the way you would say them to a colleague.

The captioned video runs 2 minutes 54 seconds. Every number comes from `docs/RESULTS.md`, `docs/BENCHMARK.md` and `docs/SECURITY_CHECKS.md`. Read them as they appear on screen.

| Scene | Time | On screen | Say |
| --- | --- | --- | --- |
| Hook | 0:01 to 0:06 | Home, the hero | "The paperwork says fifty. The dock got forty-six." |
| Promise | 0:06 to 0:23 | Home, the hero | "I'm Sriharsan. Relayloom is autonomous accounts payable that checks the goods, not just the paperwork. Meta's Muse Glimmer reads the bill. Meta's SAM 3.1 counts what actually arrived. Both run on this laptop." |
| Why it matters | 0:23 to 0:41 | Who we are, why we matter, why you need us, then the three sources | "Paying for goods that never arrived is an improper payment in U.S. law, and auditors keep finding invoices approved with no proof of receipt. Matching paperwork only proves the documents agree with each other." |
| A batch | 0:41 to 0:52 | Demo, Today | "Six bills ran by themselves. Green means entered and checked, with no person involved. Amber means someone decides." |
| The gap | 0:52 to 1:05 | Demo, the short delivery | "The bill says fifty cartons. SAM 3.1 counted the dock photos: twenty-eight and eighteen. A repeated photo is counted once. That is forty-six." |
| The cause | 1:05 to 1:15 | Demo, likely cause | "The Investigator names the likely cause, who is probably responsible, and how sure the records let it be." |
| The evidence | 1:15 to 1:26 | Demo, citations lighting up | "No claim stands without its evidence. Every statement cites a record or a photo, and code checks each citation before anyone reads it." |
| The decision | 1:26 to 1:35 | Demo, approvals | "The policy holds the bill for the owner. One key approves, and only then does a dispute go out." |
| Proof | 1:35 to 1:50 | Proof, security controls | "Every number here came from our own runs. Eleven security controls pass their checks, and together they add about thirty milliseconds to a case." |
| The result | 1:50 to 2:07 | Proof, benchmark | "On a demo set of thirty deliveries, paperwork alone caught five of seventeen bad bills and paid sixty thousand rupees wrongly. With the goods in the loop: seventeen of seventeen, and nothing paid wrongly." |
| Tamper evidence | 2:07 to 2:19 | Proof, receipt verifier | "Every step is a signed receipt. Change one recorded decision and the chain breaks at that step. The audit trail is tamper-evident." |
| Video and phone | 2:19 to 2:38 | Home, video evidence and phone alerts | "A dock video is detected a quarter of a second after the first movement. SAM 3.1 counts the steady views, and a phone on the local network gets the alert. No internet needed." |
| Boundary | 2:38 to 2:46 | Home, Docker evidence | "Network isolated: no route out, and every refused request is logged." |
| Close | 2:46 to 2:54 | Home, the close | "Pay for what arrived. Prove it. Relayloom, at relayloom dot vercel dot app. The code is open source." |

Notes for recording:
- Say "network isolated". Do not say "air gapped" unless `docs/OFFLINE_RUN.md` exists, and then read its date aloud.
- The dock video in the demo is a demo clip made from two photographs. Say "a dock video", show the two steady views and the 46 of 50, and do not
  claim a warehouse camera.
- In the replay the bill values come from the bill record and the dispute text from the recorded run. If you mention the model there, point at the
  Muse Glimmer timings on the Proof page.
- Findings are written by code from the evidence, with every citation checked.
- Real timings: on this laptop's CPU Muse Glimmer reads a bill in 4 min 33 s to 8 min 51 s and SAM 3.1 counts a photo in about 41 s. Bills run as a
  background batch.
