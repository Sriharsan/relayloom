# Demo video script: 3 minutes, working product only

Rules from the organizers (Cerebral Valley, Discord, 4 November): 3:00 or less, English, hosted and playable without logging in, real screen footage of the working product,
**live Meta model calls visible** (a terminal log or the on-screen result of a live request that names the model), the end to end flow first, no intro and no pitch,
and an opening line that says what existed before the event and what was built this week. An AI voice is allowed, a person is preferred.

Total about 430 spoken words, which is 2 minutes 50 seconds at an easy pace. Practise it once with a timer. The recording rows say what is on screen.

## The script

| Time | On screen | Say |
| --- | --- | --- |
| 0:00 to 0:14 | Terminal, large font, the command typed and run live | "Before this week there was only a written plan. This week I built Relayloom: agents that read a bill, count the goods with Meta's SAM 3.1, and look for damage with Muse Glimmer, before anything is paid." |
| 0:14 to 0:52 | **Live Meta model calls.** The terminal runs `relayloom check --bill bill.pdf --photos dock/ --po po.json --agent --condition`. The log lines name Muse-Glimmer-30B and SAM 3.1. Put a small caption on screen: "live run, sped up" if you cut the wait. | "This is a live run on my machine. Muse Glimmer 30B reads the bill into a strict form. Muse Glimmer proposes the words, SAM 3.1 outlines and numbers every item, and Glimmer looks at its own picture to confirm the count. The bill says fifty. The count is forty six. The bill is held, and the reason is written in plain words." |
| 0:52 to 1:30 | Browser: relayloom.vercel.app/try. Pick "Short delivery", then "Add photo evidence", tap items on the photo, show the verdict change, press Sign a receipt in the phone, press Save the PDF report, open the PDF. | "Anyone can try it. Enter the bill, add a photo of the goods, and tap each item. The verdict changes live. The phone signs a receipt, and the PDF report says what happened in plain words, with the photo attached. Nothing leaves the device." |
| 1:30 to 2:00 | Browser: Demo page. "Watch it count", the green marks sweeping across a real photo. Then the Case tab, the Investigator citations, then the Proof page: change one decision, the chain breaks. | "On the demo page you watch SAM count a real photo. The Investigator cites a record for every claim. Every step is signed and chained. Change one decision, and the chain breaks." |
| 2:00 to 2:20 | Terminal or Try page: damaged goods example, "9 of 60 damaged". | "Damaged goods are caught too. Glimmer looked at dented cans and torn sacks and found them, and it found nothing on the clean photos. Damaged units never count as received." |
| 2:20 to 2:45 | Proof page: the 17 of 17 table, then the Real cases strip, New Jersey nine and a half million dollars. | "On thirty deliveries, paperwork alone caught five of seventeen bad bills. With the goods in the loop it caught all seventeen and paid nothing wrongly. It passes three hundred sixty nine cases on real California purchase orders. These real cases show why it matters: a supplier billed for goods that never came, for nine years." |
| 2:45 to 2:58 | The trust line on the home page, then the PyPI page. | "No photo, no receipt, no proof, no payment. That is trust, and that is Relayloom. It is on PyPI today: pip install relayloom." |

## Recording checklist

1. Record the screen at 1080p. Make the terminal and browser text large. Close notifications.
2. Live Meta model calls. Option A, recommended: on the Kaggle free GPU the notebook shows the bill read in about 24 seconds once warm and SAM counting in about a second, so the whole live call fits in the take. Option B: run it on your laptop, where the bill read takes minutes, and cut the wait with a visible "sped up" caption. Either way the log must show the model names on screen.
3. Start Muse Glimmer first with `relayloom models serve`, and run `relayloom doctor` once so SAM is loaded. Run the command in the video from a folder with `bill.pdf`, `dock/` and `po.json`.
4. On the phone: scan the QR code on the Try page with your phone camera, or show the page in a narrow browser window. Show the camera button for the evidence photo.
5. The video must be unlisted on YouTube and play in a logged out private window. The submission closes Wednesday 4 November, 9:00 PM Eastern, with no grace period.
6. Keep every sentence short. Do not read the table. Say the numbers slowly: "seventeen of seventeen", "three hundred sixty nine".

## Do not say

Do not say "real time" for the counting. Do not say the page runs the models: the page runs the rules, and the models run on a machine or a free GPU. Do not call the demo cases customers.
