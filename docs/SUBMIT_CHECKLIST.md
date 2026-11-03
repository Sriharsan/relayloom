# Submission checklist

Deadline: **Wednesday 4 November 2026, 9:00 PM Eastern (Thursday 5 November, 7:30 AM IST).** Late submissions are not considered. Aim for
Wednesday evening IST.

## Done and verified

- Code on GitHub, public, one author: https://github.com/Sriharsan/relayloom
- Live site: https://relayloom.vercel.app (Home, Demo, Proof)
- Tests: 86 Python tests and 14 browser logic tests, and the checks workflow runs them on Linux and Windows
- Muse Glimmer 30B and SAM 3.1 run on this laptop, with recorded timings; no paid API
- Docker network with no route out, tested and dated (`docs/boundary-result.json`)
- Form text, X post and card, narration script, picture only demo video to speak over

## For you

1. **Phone check. Done on 3 November 2026: both the USB cable link and the Wi-Fi link opened on a real phone and showed the alerts.** To repeat it: On the laptop: `python -m relayloom.ap --batch --phone`. It prints a link. Open it on your phone on the same
   Wi-Fi. When a delivery needs the owner, the alert appears on the phone within a second. Tell me if anything looks wrong.
2. **Wi-Fi off check (12 minutes).** Optional, and the only way to say "tested fully disconnected": `python scripts/offline_check.py`, switch Wi-Fi
   off when it asks, switch it back on when it says Done.
3. **Video, in your own voice.** The demo should be felt and delivered by a human, so speak it. Play `relayloom-demo-picture-only.mp4`, read
   `docs/VIDEO_SCRIPT.md` over it, record your voice, then run `python scripts/add_voice.py your-voice.m4a`. Or record yourself live with
   Xbox Game Bar (Win+G) or OBS. Keep it at or under three minutes. Upload to YouTube as Unlisted and send me the link, and I add it to the site and
   the README.
4. **X post.** Post the text in `docs/X_POST.md` with `docs/x/x-card.png` and the video. Copy the post link.
5. **Submit** on the Cerebral Valley platform: repository link, live site link, video link, X post link, and the text in
   `docs/SUBMISSION_FORM_TEXT.md`. Track: Startups. Theme: Push the Frontier. Check the repository is public and the video opens in a private window.

## After submitting

Make no more commits. Judges may check commit dates, and the building period ends at the deadline.
