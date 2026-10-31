"""The one way out: an HTTPS CONNECT gateway that allows only hosts named in the policy and logs everything.

Run: python -m relayloom.ap.gateway --port 3128 --log data/gateway.jsonl
Every request is logged with time, host, decision, bytes each way and what the caller declared it
sent (model, masks) in X-Relayloom-* headers. Anything not in the policy gets 403 and is logged too.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import select
import socket
import socketserver
import threading
import time

from .policy import load_policy


class Gateway(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, allowed_hosts, log_path: Path, connect=socket.create_connection):
        self.allowed = set(allowed_hosts)
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_lock = threading.Lock()
        self.connect = connect
        self.enabled = True
        super().__init__(address, GatewayHandler)

    def record(self, entry: dict):
        entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **entry}
        with self.log_lock, self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return entry


class GatewayHandler(socketserver.StreamRequestHandler):
    def handle(self):
        request = self.rfile.readline(4096).decode("latin-1").strip()
        headers = {}
        while True:
            line = self.rfile.readline(4096).decode("latin-1").strip()
            if not line:
                break
            name, _, value = line.partition(":")
            headers[name.strip().lower()] = value.strip()
        parts = request.split()
        method = parts[0] if parts else ""
        target = parts[1] if len(parts) > 1 else ""
        host, _, port = target.rpartition(":") if method == "CONNECT" else (target, "", "")
        declared = {"model": headers.get("x-relayloom-model", ""), "masks": headers.get("x-relayloom-masks", ""),
                    "case": headers.get("x-relayloom-case", "")}
        if method != "CONNECT" or port != "443":
            self.server.record({"host": target[:200], "method": method, "decision": "blocked: only HTTPS CONNECT", **declared})
            self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
            return
        if not self.server.enabled:
            self.server.record({"host": host, "method": method, "decision": "blocked: gateway cut", **declared})
            self.wfile.write(b"HTTP/1.1 503 Gateway Cut\r\nContent-Length: 0\r\n\r\n")
            return
        if host not in self.server.allowed:
            self.server.record({"host": host, "method": method, "decision": "blocked: host not in policy", **declared})
            self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
            return
        try:
            upstream = self.server.connect((host, 443), timeout=15)
        except OSError as error:
            self.server.record({"host": host, "method": method, "decision": f"allowed, connect failed: {type(error).__name__}", **declared})
            self.wfile.write(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
            return
        self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        self.wfile.flush()
        sent = received = 0
        client = self.connection
        with upstream:
            while True:
                ready, _, _ = select.select([client, upstream], [], [], 60)
                if not ready:
                    break
                if client in ready:
                    data = client.recv(65536)
                    if not data:
                        break
                    upstream.sendall(data)
                    sent += len(data)
                if upstream in ready:
                    data = upstream.recv(65536)
                    if not data:
                        break
                    client.sendall(data)
                    received += len(data)
        self.server.record({"host": host, "method": method, "decision": "allowed", "bytes_out": sent,
                            "bytes_in": received, **declared})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3128)
    parser.add_argument("--log", type=Path, default=Path("data/gateway.jsonl"))
    args = parser.parse_args()
    policy = load_policy()
    server = Gateway((args.host, args.port), policy.allowed_hosts, args.log)
    print(f"gateway on {args.host}:{args.port}, allowed: {', '.join(policy.allowed_hosts)}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
