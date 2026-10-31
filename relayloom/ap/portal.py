"""A synthetic supplier portal inside the boundary, and the browser agent that files disputes on it."""
from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
import urllib.parse
import urllib.request

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Supplier portal (synthetic)</title>
<style>body{{font:15px system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 16px;color:#1d2330}}
label{{display:block;margin:14px 0 4px;font-weight:600}}input,textarea{{width:100%;padding:10px;font:inherit;border:1px solid #aab;border-radius:6px}}
textarea{{height:150px}}button{{margin-top:16px;padding:12px 20px;font:inherit;font-weight:600;background:#264;color:#fff;border:0;border-radius:6px}}
.note{{color:#556;font-size:13px}}.done{{padding:14px;background:#e8f4ec;border-radius:6px}}</style></head><body>
<h1>Delivery dispute</h1><p class="note">Synthetic supplier portal for the Relayloom demo. Runs on this machine only.</p>{body}</body></html>"""
FORM = """<form method="post" action="/disputes">
<label for="supplier">Supplier</label><input id="supplier" name="supplier" required>
<label for="bill_no">Bill number</label><input id="bill_no" name="bill_no" required>
<label for="po_number">Purchase order</label><input id="po_number" name="po_number" required>
<label for="message">Message</label><textarea id="message" name="message" required></textarea>
<button type="submit" id="send">Send dispute</button></form>"""


class Portal(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int = 8890):
        self.disputes: list[dict] = []
        self.lock = threading.Lock()
        super().__init__(("127.0.0.1", port), PortalHandler)

    def start(self):
        threading.Thread(target=self.serve_forever, daemon=True, name="portal").start()
        return self


class PortalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def send(self, status, body, kind="text/html; charset=utf-8"):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/disputes.json":
            with self.server.lock:
                return self.send(200, json.dumps(self.server.disputes), "application/json")
        self.send(200, PAGE.format(body=FORM))

    def do_POST(self):
        length = min(int(self.headers.get("Content-Length", 0)), 8192)
        form = {k: v[0] for k, v in urllib.parse.parse_qs(self.rfile.read(length).decode()).items()}
        with self.server.lock:
            reference = f"DSP-{len(self.server.disputes) + 1:04d}"
            self.server.disputes.append({"reference": reference, **{k: form.get(k, "") for k in
                                         ("supplier", "bill_no", "po_number", "message")}})
        self.send(200, PAGE.format(body=f'<div class="done" id="done">Received. Reference <b id="ref">{reference}</b> '
                                        f'for bill {html.escape(form.get("bill_no", ""))}.</div>'))


class BrowserDisputer:
    """Playwright fills the portal form. The text is Muse Glimmer's draft; the clicks are code."""

    def __init__(self, url: str, shots: Path):
        self.url = url.rstrip("/")
        self.shots = Path(shots)
        self.online = True

    def submit(self, case) -> dict:
        if not self.online:
            raise ConnectionError("portal link is cut")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return self.submit_without_browser(case)
        self.shots.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 900, "height": 900})
            page.goto(self.url + "/")
            page.fill("#supplier", case.supplier_id)
            page.fill("#bill_no", case.bill_no)
            page.fill("#po_number", case.po_number)
            page.fill("#message", case.dispute["text"])
            filled = self.shots / f"{case.bill_no}-dispute-filled.png"
            page.screenshot(path=str(filled))
            page.click("#send")
            page.wait_for_selector("#ref")
            reference = page.inner_text("#ref")
            browser.close()
        self.readback(case, reference)
        return {"reference": reference, "filled_by": "code (Playwright)", "seconds": round(time.perf_counter() - started, 1),
                "screenshot": filled.name, "portal_readback": "found"}

    def submit_without_browser(self, case) -> dict:
        """Where Playwright is not installed (the boundary container), post the same form directly."""
        started = time.perf_counter()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        form = urllib.parse.urlencode({"supplier": case.supplier_id, "bill_no": case.bill_no,
                                       "po_number": case.po_number, "message": case.dispute["text"]}).encode()
        page = opener.open(urllib.request.Request(self.url + "/disputes", data=form), timeout=10).read().decode()
        reference = page.split('id="ref">')[1].split("<")[0]
        self.readback(case, reference)
        return {"reference": reference, "filled_by": "code (HTTP form post, no browser)",
                "seconds": round(time.perf_counter() - started, 1), "portal_readback": "found"}

    def readback(self, case, reference):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        stored = json.loads(opener.open(self.url + "/disputes.json", timeout=10).read())
        if not any(d["reference"] == reference and d["bill_no"] == case.bill_no and d["message"] == case.dispute["text"]
                   for d in stored):
            raise RuntimeError("portal readback does not show the dispute as sent")
