"""Record the three minute demo of the live site, with captions, as an MP4.

Usage: python scripts/record_demo_video.py [--site https://relayloom.vercel.app] [--out docs/video]
It opens the real pages in a browser and walks the story in docs/VIDEO_SCRIPT.md. The captions say what is on screen, so the video
can be uploaded as it is, or used as the picture while the founder speaks the narration.
"""
import glob
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[1:]
SITE = args[args.index("--site") + 1] if "--site" in args else "https://relayloom.vercel.app"
OUT = Path(args[args.index("--out") + 1]) if "--out" in args else ROOT / "docs" / "video"
W, H = 1440, 810

CAPTION_JS = """(text) => {
  let el = document.getElementById('demo-caption');
  if (!el) {
    el = document.createElement('div'); el.id = 'demo-caption';
    el.style.cssText = 'position:fixed;left:50%;bottom:26px;transform:translateX(-50%);max-width:1120px;z-index:99999;text-align:center;' +
      'background:rgba(11,13,16,.92);color:#e7eaee;border:1px solid #2f353d;border-radius:14px;padding:14px 24px;' +
      'font:500 25px/1.35 Candara,"Nunito Sans",Calibri,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.45)';
    document.body.appendChild(el);
  }
  el.textContent = text; el.style.display = text ? 'block' : 'none';
}"""

SCROLL_JS = """([target, ms]) => new Promise(resolve => {
  const y0 = window.scrollY;
  const el = typeof target === 'string' ? document.querySelector(target) : null;
  const y1 = typeof target === 'number' ? target : (el ? el.getBoundingClientRect().top + window.scrollY - 84 : y0);
  const t0 = performance.now();
  const ease = t => t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
  const step = now => { const t = Math.min(1, (now - t0) / ms); window.scrollTo(0, y0 + (y1 - y0) * ease(t)); t < 1 ? requestAnimationFrame(step) : resolve(); };
  requestAnimationFrame(step);
})"""


LOCATOR_SCROLL_JS = """(el, ms) => new Promise(resolve => {
  const y0 = window.scrollY, y1 = el.getBoundingClientRect().top + window.scrollY - 84, t0 = performance.now();
  const ease = t => t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
  const step = now => { const t = Math.min(1, (now - t0) / ms); window.scrollTo(0, y0 + (y1 - y0) * ease(t)); t < 1 ? requestAnimationFrame(step) : resolve(); };
  requestAnimationFrame(step);
})"""


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.webm"):
        old.unlink()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(OUT), record_video_size={"width": W, "height": H})
        page = context.new_page()

        started = time.time()
        scenes = []

        def say(text, seconds):
            scenes.append({"at_s": round(time.time() - started, 1), "caption": text})
            page.evaluate(CAPTION_JS, text)
            page.wait_for_timeout(int(seconds * 1000))

        def scroll_to(locator, ms=1400):
            locator.first.evaluate(LOCATOR_SCROLL_JS, ms)

        def scroll(target, ms=1400):
            page.evaluate(SCROLL_JS, [target, ms])

        def ring(selector):
            page.evaluate("(s) => { document.querySelectorAll('.guide-ring').forEach(e => e.classList.remove('guide-ring')); const e = document.querySelector(s); if (e) e.classList.add('guide-ring'); }", selector)

        # 1. the hook, the company, the promise
        page.goto(SITE + "/", wait_until="networkidle")
        say("The paperwork says 50. The dock got 46.", 5)
        say("Relayloom: autonomous accounts payable that checks the goods, not just the paperwork.", 15)
        # 2. who, why it matters, why you need us
        scroll(".bg-surface\\/40", 1600)
        say("Who we are. Why we matter. Why you need us.", 8)
        scroll("#stakes", 1600)
        say("The risk is written into law and into every audit. Three primary sources.", 8)
        # 3. the guided demo
        page.goto(SITE + "/demo", wait_until="networkidle")
        page.wait_for_timeout(600)
        say("Six bills ran by themselves. Green means entered and checked. Amber means a person decides.", 10)
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(900)
        say("The bill says 50. SAM 3.1 counted the dock photos: 28 and 18. A repeated photo is counted once. That is 46.", 12)
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(900)
        say("The Investigator names the likely cause, who is probably responsible, and how sure the records let it be.", 9)
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(900)
        page.locator("#guide-finding button").first.click()
        say("Every statement cites a record or a photo. Code checks each citation before anyone reads the finding.", 10)
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(900)
        page.keyboard.press("a")
        say("One key approves. A dispute goes out only after the owner decides.", 8)
        # 4. the proof
        page.goto(SITE + "/proof", wait_until="networkidle")
        say("Every number on this page came from our own runs.", 4)
        scroll_to(page.get_by_text("Every control passed its check, and none slows the work"), 1600)
        say("Eleven security controls pass their checks, and together they add about 30 milliseconds to a case.", 8)
        scroll_to(page.get_by_text("With the goods in the loop, more errors are caught"), 1600)
        say("Paperwork alone caught 5 of 17 bad bills and paid 60,035 rupees wrongly. With the goods in the loop: 17 of 17, and nothing paid wrongly.", 15)
        scroll_to(page.get_by_text("Check the chain in your own browser"), 1600)
        say("Every step is a signed receipt. Change one recorded decision...", 5)
        page.get_by_role("button", name="Change one decision and verify again").click()
        say("...and the chain breaks at that step. The audit trail is tamper-evident.", 6)
        page.get_by_role("button", name="Restore the receipts").click()
        page.wait_for_timeout(500)
        # 5. video, phone, boundary
        page.goto(SITE + "/", wait_until="networkidle")
        scroll_to(page.locator("#video"), 10)
        say("A dock video is detected a quarter of a second after the first movement. SAM 3.1 counts the steady views.", 9)
        scroll_to(page.locator("#phone"), 1600)
        say("Alerts reach a phone on the local network. No internet needed.", 6)
        scroll_to(page.get_by_text("Tested in Docker, no route out"), 1600)
        say("Network isolated: no route out, and every refused request is logged.", 6)
        # 6. close
        scroll(100000, 2600)
        say("Pay for what arrived. Prove it.  relayloom.vercel.app", 8)
        video = page.video.path()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "scenes.json").write_text(json.dumps({"seconds": round(time.time() - started, 1), "scenes": scenes}, indent=1), encoding="utf-8")
        context.close()
        browser.close()
    return Path(video)


def to_mp4(webm: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg") or (glob.glob(str(Path.home() / "AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin/ffmpeg.exe")) or [None])[0]
    if not ffmpeg:
        print("ffmpeg not found; the WebM file is kept:", webm)
        return webm
    mp4 = OUT / "relayloom-demo-captioned.mp4"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(webm), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                    "-movflags", "+faststart", str(mp4)], check=True)
    return mp4


if __name__ == "__main__":
    webm = run()
    final = to_mp4(webm)
    print("video:", final, f"{final.stat().st_size / 1e6:.1f} MB")
