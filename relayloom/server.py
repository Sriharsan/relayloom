"""Loopback-only web delivery with same-origin mutation and room boundaries."""
from __future__ import annotations

from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit

from .controller import Controller, Rejected, packed

WEB = Path(__file__).resolve().parent.parent / "web"
COOKIE = "relayloom_session"
MAX_BODY = 8192


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 16

    def __init__(self, address, controller):
        if address[0] not in ("127.0.0.1", "::1", "localhost"):
            raise ValueError("This rehearsal server must bind to loopback. Remote hosting needs a separate security boundary.")
        self.controller = controller
        self.stream_slots = threading.BoundedSemaphore(12)
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "Relayloom"
    sys_version = ""

    def log_message(self, format, *args):
        # Never log session, invite, request body, or user-provided text.
        return

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def headers_common(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")

    def response(self, status, value, cookie=None):
        body = packed(value).encode()
        self.send_response(status)
        self.headers_common()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie is not None:
            self.send_header("Set-Cookie", f"{COOKIE}={cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age={28800 if cookie else 0}")
        self.end_headers()
        self.wfile.write(body)

    def local_origin(self, mutation=False):
        expected_port = self.server.server_address[1]
        try:
            host = urlsplit("http://" + self.headers.get("Host", ""))
            if host.hostname not in ("127.0.0.1", "localhost", "::1") or host.port != expected_port or host.username or host.password or host.path or host.query or host.fragment:
                raise ValueError()
            origin = self.headers.get("Origin")
            if origin:
                parsed = urlsplit(origin)
                if parsed.scheme != "http" or parsed.netloc != host.netloc or parsed.path or parsed.query or parsed.fragment:
                    raise ValueError()
            # Browser cross-origin requests cannot reach mutations with no Origin.
            # Non-browser clients may omit it but still need their scoped CSRF token.
            if mutation and self.headers.get("Sec-Fetch-Site") in ("cross-site", "same-site"):
                raise ValueError()
        except (ValueError, TypeError):
            raise Rejected("Use this workroom's local address and same-origin page.", 403)

    def token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except CookieError:
            return ""
        return cookie[COOKIE].value if COOKIE in cookie else ""

    def body(self):
        if self.headers.get("Transfer-Encoding"):
            raise Rejected("Streaming request bodies are not supported.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise Rejected("Invalid request length.")
        if length > MAX_BODY:
            # Drain only a bounded small rejection body. Closing a Windows socket
            # with unread inbound bytes can discard the 413 response as a reset.
            self.rfile.read(min(length, 65536))
            raise Rejected("Request must contain at most 8 KB of JSON.", 413)
        if length <= 0:
            raise Rejected("Request must contain at most 8 KB of JSON.", 413)
        if self.headers.get("Content-Type", "").split(";", 1)[0].lower() != "application/json":
            raise Rejected("Send JSON for this action.", 415)
        try:
            value = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            raise Rejected("The request could not be read as JSON.")
        if not isinstance(value, dict):
            raise Rejected("Send a JSON object.")
        return value

    def do_GET(self):
        try:
            self.local_origin()
            path = urlsplit(self.path).path
            if path == "/api/session":
                self.response(200, self.server.controller.session(self.token()))
            elif path == "/api/state":
                self.response(200, self.server.controller.snapshot(self.token()))
            elif path == "/api/events":
                self.events()
            else:
                asset = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}.get(path)
                if asset is None:
                    raise Rejected("This page was not found.", 404)
                body = (WEB / asset[0]).read_bytes()
                self.send_response(200)
                self.headers_common()
                self.send_header("Content-Type", asset[1] + "; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Rejected as error:
            self.response(error.status, {"error": str(error)})
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            return

    def do_POST(self):
        try:
            self.local_origin(mutation=True)
            path = urlsplit(self.path).path
            body = self.body()
            controller = self.server.controller
            if path in ("/api/rooms", "/api/join"):
                # Do not let another tab silently replace an active identity.
                if controller.session(self.token())["signed_in"]:
                    raise Rejected("Sign out before creating or joining another workroom.", 409)
                token = controller.create(body) if path == "/api/rooms" else controller.join(body)
                self.response(201, {"ok": True}, token)
            elif path.startswith("/api/"):
                action = path[5:]
                result = controller.mutate(self.token(), self.headers.get("X-Relayloom-CSRF", ""), action, body)
                self.response(200, result, "" if action == "logout" else None)
            else:
                raise Rejected("Unknown action.", 404)
        except Rejected as error:
            self.response(error.status, {"error": str(error)})
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            return
        except Exception:
            self.response(500, {"error": "The action could not be completed. Review the current workroom and retry."})

    def events(self):
        controller, token = self.server.controller, self.token()
        controller.snapshot(token)  # Authenticate before starting a successful stream.
        if not self.server.stream_slots.acquire(blocking=False):
            raise Rejected("Too many open activity streams; close an unused tab.", 429)
        try:
            self.send_response(200)
            self.headers_common()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            previous = None
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                try:
                    state = controller.snapshot(token)  # Recheck session and membership on every tick.
                except Rejected:
                    return
                encoded = packed(state)
                if encoded != previous:
                    self.wfile.write(f"event: state\ndata: {encoded}\n\n".encode())
                    self.wfile.flush()
                    previous = encoded
                time.sleep(0.3)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            return
        finally:
            self.server.stream_slots.release()
