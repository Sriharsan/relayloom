# Submission checklist

Deadline: **Wednesday 4 November 2026, 9:00 PM Eastern (Thursday 5 November, 7:30 AM IST).** Late submissions are not considered. Aim for a submittable
version pushed by 6:00 PM IST on the 4th, then freeze at 4:00 AM IST on the 5th. Make no commits after submitting.

## Done and verified

- Code on GitHub, public, one author: https://github.com/Sriharsan/relayloom. Secret scan of every tracked file and all history is clean, `.env` is ignored, and a fresh clone passes the tests and every check.
- Live site: https://relayloom.vercel.app (Home, Demo, Proof, Developers), headings and body in Figtree, no horizontal scroll at 390 px.
- Tests: 128 Python tests, 14 browser logic tests, 44 command line scenarios, 369 real-order cases, and the checks workflow on Linux and Windows.
- Muse Glimmer 30B and SAM 3.1 run on this laptop (CPU) and on a free Kaggle GPU (two T4s), with recorded timings. No paid API.
- Docker network with no route out, and a fully disconnected run on 3 November (`docs/OFFLINE_RUN.md`).
- Phone alerts verified on a real phone (3 November), with photo upload from the phone page.
- English, Tamil and Hindi for the phone alerts and the approval screen: `docs/LANGUAGES.md`.
- Package `relayloom` 0.4.0: builds, passes the PyPI check, installs and runs with the network blocked (`docs/PACKAGE_CHECK.md`).
- Real cases from courts, audits and news with their sources: `docs/SOURCES.md`.

## For you

1. **Language check (15 minutes).** Open `docs/LANGUAGES.md`, read the Tamil and Hindi column, fix any word, tick the last column. Tell me what to change.
   Opening the phone page or the approval screen with `?review=1` underlines every string that is still unchecked.
2. **Phone check of the languages.** On the phone page pick தமிழ் or हिन्दी and read the alerts.
3. **Video, in your own voice.** Read `docs/VIDEO_SCRIPT.md` (it opens on the New Jersey case and the ISKCON case, an allegation) over the picture, then run
   `python scripts/add_voice.py your-voice.m4a`, or record yourself live. Keep it at or under three minutes. Upload to YouTube as Unlisted and send me the link.
4. **PyPI publish.** `python -m pip install twine`, then from the repository folder: `python -m build` and `python -m twine upload dist/*` with `TWINE_USERNAME=__token__`
   and `TWINE_PASSWORD` set to your token in the same window (do not paste the token in chat). After it is live: `python -m pip install relayloom` in a clean environment.
5. **X post.** Post `docs/X_POST.md` with `docs/x/x-card.png` and the video. Copy the post link.
6. **Submit** on the Cerebral Valley platform: repository link, live site link, video link, X post link, and the text in `docs/SUBMISSION_FORM_TEXT.md`.
   Track: Startups. Theme: Push the Frontier. Check the repository is public and the video opens in a private window.

## After submitting

Make no more commits. Judges may check commit dates, and the building period ends at the deadline.
