# Video script (3 minutes)

Shows only work built from 27 October. Screens come from https://relayloom.vercel.app (Demo and Proof pages). Say plainly what is
recorded: the SAM 3.1 counts and Muse Glimmer timings on screen come from real runs on one laptop CPU and are replayed with their
date and timings. Numbers come from `docs/BENCHMARK.md` and
`docs/RESULTS.md`; read them from the screen, do not round them up. No savings, customer or industry numbers.

| Time | On screen | Say |
| --- | --- | --- |
| 0:00 | Case screen for bill CAL-0990: the bill line "50 cartons" next to the two photos with 28 and 18 counted | "The paperwork says 50. The dock got 46." |
| 0:12 | The Today screen: bills moving through Read, Count, Match, Investigate, Enter, Check | "Relayloom is autonomous accounts payable that checks the goods, not just the paperwork. Agents read the bill, look at what arrived, and investigate any gap with evidence." |
| 0:25 | Investigation panel: the finding, click two citations (a photo, an earlier invoice) | "Every statement cites a record or a photo, and code checks each citation exists before anyone sees the finding. It recounted both photos, ignored a repeated photo, and found this supplier billed 40 and the dock counted 38 on an earlier order." |
| 0:55 | Approvals tab: the proposal next to the policy decision, the dispute draft preview, press A | "It proposes a dispute for the four missing cartons. The policy says this needs the owner. One key approves, and the dispute goes out only after that." |
| 1:15 | A matching delivery entered and checked with no person; the split delivery matching as a running total; the duplicate bill held | "A matching delivery is entered and read back by a separate checker with nobody involved. One order that arrived in two deliveries still matches. The same goods billed again under a new number are held." |
| 1:40 | Benchmark page: table A against B, then the caveat | "On a synthetic set built by us, paperwork only against paperwork plus goods. Here is what each caught and missed, in our own numbers." Read the table values as shown. |
| 2:05 | Case with hidden text: the white text revealed, the receipt line, the payment details from the ledger | "White text on a bill asked to pay a new account. It never reached the model, and payment details come only from the supplier master." |
| 2:20 | Today screen: cut network, cases show "held, offline", reconnect, the ledger is read first, no duplicate | "Cut the network and nothing is entered or sent. Reconnect and the ledger is read first, so there is no duplicate." |
| 2:40 | Boundary page and the verifier in the browser | "Private numbers are masked before any model sees them. Muse Glimmer and SAM 3.1 run on this machine. Every step is a signed receipt you can verify offline." |
| 2:52 | Title card | "Relayloom. Autonomous accounts payable that checks the goods, not just the paperwork." |

Notes for recording:
- Say "network isolated", never "air gapped", unless a run with the network physically disconnected is shown and dated.
- Show the real timings. Muse Glimmer takes several minutes per bill and SAM 3.1 about a minute per photo on this CPU.
- Video counting is not built. Do not mention it except as planned.
- In the site replay the bill values come from the bill record and the dispute text comes from a template. Do not say Muse Glimmer
  wrote that text. Muse Glimmer's real readings and timings are on the Proof page; point at them if you mention the model.
- The benchmark findings are written by code from the evidence. Say so if you describe them.
- Do not claim a Docker no route out run or a disconnected run. Neither has been done.
