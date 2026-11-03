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
poll();
</script></body></html>"""


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

    def do_POST(self):  # read only: no approvals, no changes
        self.reply(405, "text/plain; charset=utf-8", b"read only")


class PhoneServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, hub: AlertHub, token: str | None = None, wait: float = 20.0):
        self.hub, self.token, self.wait = hub, token or secrets.token_urlsafe(16), wait
        super().__init__(address, PhoneHandler)

    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self.serve_forever, daemon=True, name="phone-alerts")
        thread.start()
        return thread

    def link(self, host: str) -> str:
        return f"http://{host}:{self.server_address[1]}/?t={self.token}"
