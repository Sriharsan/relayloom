"""Screenshot every app screen at 1440 and 390 px with Playwright, plus a quick horizontal overflow check.

Usage: python scripts/screenshots.py [OUTDIR]   (needs python -m relayloom.ap running on 8800)
"""
import json
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/shots")
BASE = "http://127.0.0.1:8800"
OUT.mkdir(parents=True, exist_ok=True)
state = json.loads(__import__("urllib.request").request.urlopen(BASE + "/api/state").read())
ids = {c["id"] for c in state["cases"]}
pages = [("today", "#today"), ("approvals", "#approvals"), ("boundary", "#boundary")]
for name in ("match", "short", "injection"):
    if name in ids:
        pages.append((f"case-{name}", f"#case/{name}"))
problems = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in ((1440, 900), (390, 844)):
        for theme in ("dark", "light"):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(BASE + "/#today")
            page.evaluate(f"document.documentElement.dataset.theme='{theme}'")
            for name, hash_ in pages:
                if theme == "light" and name not in ("today", "case-match"):
                    continue
                page.goto(BASE + "/" + hash_)
                page.wait_for_timeout(1800)
                over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                if over > 0:
                    problems.append(f"{name} at {width}: page scrolls sideways by {over}px")
                small = page.evaluate("""[...document.querySelectorAll('button, a.link, nav a')].filter(e => e.offsetParent && (e.getBoundingClientRect().height < 44)).map(e => e.textContent.trim().slice(0, 20))""")
                if small:
                    problems.append(f"{name} at {width}: targets under 44px: {small}")
                page.screenshot(path=str(OUT / f"{name}-{width}-{theme}.png"), full_page=True)
            page.close()
    browser.close()
print("\n".join(problems) or "no overflow and no small targets")
