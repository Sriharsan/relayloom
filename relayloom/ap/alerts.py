"""Alerts to a phone on the same local network. Nothing leaves the building and no internet is needed.

AlertHub keeps the alerts the agents raise (a delivery needs the owner, the network was cut, hidden text tried to change
a bank account, a readback failed). PhoneServer is a separate, tiny, read only server that starts only when asked
(`--phone`). It shows the alerts on a phone page and nothing else: no approvals, no bills, no ledger. Every request needs
the random token that is printed when it starts, compared in constant time. The main app stays on loopback.
"""
from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import socket
import threading
import time
from urllib.parse import parse_qs, urlsplit


class AlertHub:
    def __init__(self):
        self.items: list[dict] = []
        self.changed = threading.Condition()

    def publish(self, kind: str, title: str, body: str, case: str = "") -> dict:
        with self.changed:
            item = {"id": len(self.items) + 1, "time": time.strftime("%H:%M:%S"), "kind": kind, "title": title,
                    "body": body, "case": case}
            self.items.append(item)
            self.changed.notify_all()
            return item

    def after(self, last_id: int, wait: float = 0.0) -> list[dict]:
        """Alerts newer than last_id. Waits up to `wait` seconds for one to arrive (long polling)."""
        with self.changed:
            if wait and not [i for i in self.items if i["id"] > last_id]:
                self.changed.wait(timeout=wait)
            return [i for i in self.items if i["id"] > last_id]


def lan_address() -> str:
    """This machine's address on the local network. Connecting a UDP socket sends no packet."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def lan_addresses() -> list[str]:
    """Every address a phone on a connected network could use, the default route first. A laptop on Wi-Fi and a USB cable has two."""
    first = lan_address()
    found = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith(("127.", "169.254.")):
                found.append(ip)
    except OSError:
        pass
    ordered = ([first] if first != "127.0.0.1" else []) + [ip for ip in dict.fromkeys(found) if ip != first]
    return ordered or [first]


def announce(server: "PhoneServer") -> None:
    """Print the phone links, one per network, and a QR code for each so a phone camera can scan it."""
    print("Phone alerts, local network only, read only. Open the link that is on the SAME network as the phone,")
    print("or scan its QR code with the phone camera. Anyone with a link sees the alerts, so keep it to yourself.", flush=True)
    for ip in lan_addresses():
        link = server.link(ip)
        print(f"\n  {link}", flush=True)
        try:
            import segno
            segno.make(link, error="m").terminal(compact=False, border=2)  # colour blocks made of spaces: safe on any console encoding
        except ImportError:
            print("  (install segno with: python -m pip install segno, to get a QR code here)", flush=True)
        except Exception:  # a QR code that cannot be drawn never stops the alerts
            print("  (the QR code could not be drawn in this window, use the link above)", flush=True)


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Relayloom alerts</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#0b0d10;color:#e7eaee;font:16px/1.45 Candara,Calibri,"Segoe UI",system-ui,sans-serif}
header{position:sticky;top:0;background:#0b0d10;border-bottom:1px solid #23282f;padding:14px 16px}
h1{margin:0;font-size:17px}#state{margin:2px 0 0;font-size:13px;color:#8a939e}
main{padding:12px 16px 40px;display:grid;gap:10px}
.empty{color:#8a939e;font-size:14px;padding:24px 0}
.card{background:#12151a;border:1px solid #23282f;border-radius:12px;padding:14px}
.card.needs_owner{border-color:#f5b54480}.card.injection,.card.readback{border-color:#ff6b6b80}
.card b{display:block;font-size:16px}.card span{display:block;margin-top:4px;color:#b8c0c9;font-size:14px}
.card small{display:block;margin-top:8px;color:#8a939e;font:12px ui-monospace,monospace}
button{min-height:44px;margin-top:6px;background:#12151a;color:#e7eaee;border:1px solid #2f353d;border-radius:8px;padding:0 14px;font:inherit}
</style></head><body>
<header><h1>Relayloom alerts</h1><p id="state">Connecting</p></header>
<section class="card" style="margin:12px 16px 0"><b>Count a delivery</b>
<span>Take a photo of the goods. The laptop counts them and the result appears below.</span>
<input id="word" value="box" aria-label="What to count" style="width:100%;min-height:44px;margin-top:8px;background:#0b0d10;color:#e7eaee;border:1px solid #2f353d;border-radius:8px;padding:0 12px;font:inherit">
<input id="shot" type="file" accept="image/*" capture="environment" style="display:none">
<button id="take" type="button">Take dock photo</button><small id="up"></small></section>
<main id="list"><p class="empty" id="empty">No alerts yet. This page lights up when a delivery needs you.</p></main>
<script>
var token=new URLSearchParams(location.search).get("t")||"",last=0,list=document.getElementById("list"),state=document.getElementById("state");
function add(a){var d=document.createElement("div");d.className="card "+a.kind;
 var b=document.createElement("b");b.textContent=a.title;var s=document.createElement("span");s.textContent=a.body;
 var m=document.createElement("small");m.textContent=a.time+(a.case?" · "+a.case:"");d.append(b,s,m);
 var e=document.getElementById("empty");if(e)e.remove();list.prepend(d);
 if(navigator.vibrate)navigator.vibrate([120,60,120]);
 if(window.Notification&&Notification.permission==="granted")new Notification(a.title,{body:a.body});}
function poll(){fetch("alerts?t="+encodeURIComponent(token)+"&after="+last).then(function(r){
 if(r.status===403){state.textContent="This link is not valid. Open the link from the laptop again.";return null}
 return r.json()}).then(function(j){if(!j)return;state.textContent="Connected, waiting for deliveries";
 j.forEach(function(a){last=Math.max(last,a.id);add(a)});poll()}).catch(function(){
 state.textContent="Reconnecting";setTimeout(poll,2000)})}
if(window.Notification&&Notification.permission==="default"){var n=document.createElement("button");
 n.textContent="Allow notifications on this phone";n.onclick=function(){Notification.requestPermission();n.remove()};
 document.querySelector("header").append(n)}
document.getElementById("take").onclick=function(){document.getElementById("shot").click()};
document.getElementById("shot").onchange=function(){var f=this.files[0],up=document.getElementById("up");if(!f)return;
 up.textContent="Sending "+Math.round(f.size/1024)+" KB to the laptop";
 fetch("photo?t="+encodeURIComponent(token)+"&word="+encodeURIComponent(document.getElementById("word").value),{method:"POST",headers:{"Content-Type":f.type||"image/jpeg"},body:f})
 .then(function(r){return r.json().then(function(j){up.textContent=r.ok?"Received. Counting on the laptop.":(j.error||"Not accepted")})}).catch(function(){up.textContent="Could not reach the laptop"});this.value=""};
poll();
</script></body></html>"""


IMAGE_TYPES = {"image/jpeg": bytes([0xFF, 0xD8, 0xFF]), "image/png": bytes([0x89]) + b"PNG", "image/webp": b"RIFF"}


class PhoneHandler(BaseHTTPRequestHandler):
    server_version = "RelayloomPhone"

    def log_message(self, format, *args):  # quiet: no tokens in logs
        pass

    def reply(self, status: int, kind: str, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        given = (query.get("t") or [""])[0]
        if not hmac.compare_digest(given.encode(), self.server.token.encode()):
            return self.reply(403, "text/plain; charset=utf-8", b"forbidden")
        if url.path == "/":
            return self.reply(200, "text/html; charset=utf-8", PAGE.encode())
        if url.path == "/alerts":
            try:
                last = int((query.get("after") or ["0"])[0])
            except ValueError:
                last = 0
            items = self.server.hub.after(last, wait=self.server.wait)
            return self.reply(200, "application/json", json.dumps(items).encode())
        self.reply(404, "text/plain; charset=utf-8", b"not found")

    def do_POST(self):  # read only, except one thing: a photo of the goods, counted on the laptop
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        if url.path != "/photo" or not hmac.compare_digest((query.get("t") or [""])[0].encode(), self.server.token.encode()):
            self.drain()
            return self.reply(405 if url.path != "/photo" else 403, "text/plain; charset=utf-8", b"read only" if url.path != "/photo" else b"forbidden")
        handler = self.server.photo_handler
        if handler is None:
            self.drain()
            return self.json_reply(404, {"error": "This laptop is not taking photos"})
        kind = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        try:
            length = int(self.headers.get("Content-Length") or "")
        except ValueError:
            return self.json_reply(411, {"error": "Length required"})
        if length <= 0 or length > self.server.max_photo:
            self.close_connection = True
            return self.json_reply(413, {"error": f"Photo must be under {self.server.max_photo // 1048576} MB"})
        body = self.rfile.read(length)
        if kind not in IMAGE_TYPES or not body.startswith(IMAGE_TYPES[kind]):
            return self.json_reply(415, {"error": "Only JPEG, PNG or WebP photos are accepted"})
        word = (query.get("word") or ["box"])[0]
        self.json_reply(202, handler(body, kind, word))

    def drain(self):
        """Read (and drop) a small refused body, so the client sees the answer instead of a reset connection."""
        try:
            remaining = min(int(self.headers.get("Content-Length") or 0), 1048576)
        except ValueError:
            return
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 65536))
            if not chunk:
                break
            remaining -= len(chunk)

    def json_reply(self, status: int, value: dict):
        self.reply(status, "application/json", json.dumps(value).encode())


class PhoneServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False  # on Windows reuse lets a second copy share the port and answer with a different token

    def __init__(self, address, hub: AlertHub, token: str | None = None, wait: float = 20.0, photo_handler=None,
                 max_photo: int = 12 * 1048576):
        self.hub, self.token, self.wait = hub, token or secrets.token_urlsafe(16), wait
        self.photo_handler, self.max_photo = photo_handler, max_photo
        super().__init__(address, PhoneHandler)

    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self.serve_forever, daemon=True, name="phone-alerts")
        thread.start()
        return thread

    def link(self, host: str) -> str:
        return f"http://{host}:{self.server_address[1]}/?t={self.token}"


class PhoneInbox:
    """Takes photos from the phone, saves them on this laptop, counts them in the background, and alerts with the result.

    `counter.count(photo, prompt, key)` is the same interface the pipeline uses, so SAM 3.1 or the look agent both fit.
    Nothing leaves the local network: the photo goes phone to laptop, and the count is shown on the phone page.
    """

    def __init__(self, folder, hub: AlertHub, counter=None):
        from pathlib import Path
        self.folder, self.hub, self.counter, self.threads = Path(folder), hub, counter, []

    def __call__(self, body: bytes, kind: str, word: str) -> dict:
        import re
        word = word.strip().lower()
        if not re.fullmatch(r"[a-z][a-z \-]{1,30}", word):
            word = "box"
        self.folder.mkdir(parents=True, exist_ok=True)
        name = time.strftime("dock-%Y%m%d-%H%M%S") + f"-{secrets.token_hex(2)}" + {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[kind]
        path = self.folder / name
        path.write_bytes(body)
        self.hub.publish("photo", "Dock photo received", f"{name}, {len(body) // 1024} KB. Counting {word}.", "phone")
        if self.counter is None:
            self.hub.publish("photo", "Photo saved, not counted", "Start the app with --counter live to count photos.", "phone")
        else:
            thread = threading.Thread(target=self.count, args=(path, word), daemon=True, name="phone-count")
            thread.start()
            self.threads.append(thread)
        return {"received": name, "word": word, "counting": self.counter is not None}

    def count(self, path, word: str):
        try:
            started = time.perf_counter()
            result = self.counter.count(path, word, path.stem)
            seconds = round(time.perf_counter() - started, 1)
            self.hub.publish("counted", f"Counted {result['count']} {word}", f"{path.name} in {seconds} s on this laptop.", "phone")
        except Exception as error:  # a failed count is an alert, never a silent miss
            self.hub.publish("readback", "Count failed", f"{path.name}: {str(error)[:120]}", "phone")
