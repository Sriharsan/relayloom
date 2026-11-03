"""Make the social preview image (link shares) and the X post card from the real counted dock frames.

Usage: python scripts/make_social_cards.py
Writes site-src/public/og.png (1200 by 630) and docs/x/x-card.png (1600 by 900).
"""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "site-src" / "public" / "img"
video = json.loads((ROOT / "site-src" / "src" / "data" / "video.json").read_text(encoding="utf-8"))
frames = video["frames"]

CARD = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0}
body{width:%(w)dpx;height:%(h)dpx;background:#0b0d10;color:#e7eaee;font-family:Candara,"Nunito Sans",Calibri,"Segoe UI",sans-serif;
 padding:%(pad)dpx;display:grid;grid-template-columns:1.05fr .95fr;gap:%(gap)dpx;align-items:center;
 background-image:linear-gradient(to right,rgba(231,234,238,.035) 1px,transparent 1px),linear-gradient(to bottom,rgba(231,234,238,.035) 1px,transparent 1px);background-size:48px 48px}
.brand{display:flex;align-items:center;gap:12px;font-size:%(brand)dpx;font-weight:600;letter-spacing:-.01em}
h1{font-size:%(h1)dpx;line-height:1.06;letter-spacing:-.03em;font-weight:700;margin-top:%(g1)dpx}
h1 span{color:#3ddc97}
p{margin-top:%(g2)dpx;font-size:%(p)dpx;line-height:1.45;color:#a3acb7;max-width:30em}
.chips{display:flex;gap:10px;margin-top:%(g2)dpx;flex-wrap:wrap}
.chip{font:600 %(chip)dpx ui-monospace,Consolas,monospace;border:1px solid #2f353d;border-radius:99px;padding:6px 14px;color:#e7eaee;background:#12151a}
.right{display:grid;gap:%(gap2)dpx}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:%(gap2)dpx}
figure{background:#12151a;border:1px solid #23282f;border-radius:16px;padding:12px}
figure img{width:100%%;display:block;border-radius:10px;aspect-ratio:4/3;object-fit:cover}
figcaption{display:flex;justify-content:space-between;align-items:baseline;margin-top:10px;font:500 %(cap)dpx ui-monospace,Consolas,monospace;color:#8a939e}
figcaption b{font-size:%(num)dpx;color:#3ddc97}
.gap{border:1px solid rgba(245,181,68,.5);background:#12151a;border-radius:16px;padding:%(gp)dpx %(gp2)dpx;display:flex;justify-content:space-between;align-items:baseline;font-size:%(p)dpx;color:#a3acb7}
.gap b{font:600 %(big)dpx ui-monospace,Consolas,monospace;color:#f5b544;white-space:nowrap}
</style></head><body>
<div><div class="brand"><svg width="%(logo)d" height="%(logo)d" viewBox="0 0 22 22" fill="none"><rect x="1" y="1" width="9" height="9" rx="2" stroke="#e7eaee" stroke-width="1.5"/><rect x="12" y="1" width="9" height="9" rx="2" stroke="#3ddc97" stroke-width="1.5"/><rect x="1" y="12" width="9" height="9" rx="2" stroke="#3ddc97" stroke-width="1.5"/><rect x="12" y="12" width="9" height="9" rx="2" stroke="#f5b544" stroke-width="1.5" stroke-dasharray="2.5 2.5"/></svg>Relayloom</div>
<h1>The paperwork says 50.<br><span>The dock got 46.</span></h1>
<p>Autonomous accounts payable that checks the goods, not just the paperwork. Muse Glimmer reads the bill, SAM 3.1 counts what arrived, and every step leaves a tamper-evident receipt.</p>
<div class="chips"><span class="chip">Meta open weights</span><span class="chip">runs on a laptop</span><span class="chip">relayloom.vercel.app</span></div></div>
<div class="right"><div class="pair">%(figures)s</div>
<div class="gap"><span>Dock count against the bill</span><b>%(total)d of %(billed)d</b></div></div>
</body></html>"""


def card(width, height, out, scale):
    figures = "".join(
        f'<figure><img src="data:image/jpeg;base64,{base64.b64encode((IMG / (f["overlay"] or f["id"] + ".jpg")).read_bytes()).decode()}"><figcaption><span>{f["id"]}</span><b>{f["count"]}</b></figcaption></figure>'
        for f in frames)
    values = {"w": width, "h": height, "pad": int(56 * scale), "gap": int(44 * scale), "gap2": int(14 * scale), "brand": int(26 * scale),
              "h1": int(54 * scale), "g1": int(26 * scale), "g2": int(22 * scale), "p": int(21 * scale), "chip": int(14 * scale),
              "cap": int(13 * scale), "num": int(26 * scale), "gp": int(16 * scale), "gp2": int(22 * scale), "big": int(34 * scale),
              "logo": int(30 * scale), "figures": figures, "total": video["total"], "billed": video["billed"]}
    html = CARD % values
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(400)
        page.screenshot(path=str(out))
        browser.close()
    print("wrote", out.relative_to(ROOT), f"{out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    card(1200, 630, ROOT / "site-src" / "public" / "og.png", 1.0)
    card(1600, 900, ROOT / "docs" / "x" / "x-card.png", 1.42)
