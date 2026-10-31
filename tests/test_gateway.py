"""The egress gateway allows only policy hosts and logs every request. No real network is used."""
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest

from relayloom.ap.gateway import Gateway
from relayloom.ap.policy import load_policy


class FakeUpstream:
    """Stands in for an allowed provider: echoes what it receives."""

    def __init__(self):
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen()
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self):
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                return
            with conn:
                data = conn.recv(1024)
                conn.sendall(b"echo:" + data)


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.log = Path(self.folder.name) / "gateway.jsonl"
        self.upstream = FakeUpstream()
        self.connected = []

        def connect(address, timeout=None):
            self.connected.append(address)
            return socket.create_connection(self.upstream.server.getsockname(), timeout=timeout)

        self.gateway = Gateway(("127.0.0.1", 0), load_policy().allowed_hosts, self.log, connect=connect)
        threading.Thread(target=self.gateway.serve_forever, daemon=True).start()

    def tearDown(self):
        self.gateway.shutdown()
        self.gateway.server_close()
        self.upstream.server.close()
        self.folder.cleanup()

    def request(self, line, payload=b""):
        with socket.create_connection(self.gateway.server_address, timeout=5) as s:
            s.sendall(line.encode() + b"\r\nX-Relayloom-Model: test-model\r\nX-Relayloom-Masks: gstin,bank_account\r\n\r\n")
            reply = s.recv(200)
            if payload and b"200" in reply:
                s.sendall(payload)
                reply += s.recv(200)
            return reply.decode()

    def entries(self):
        # A tunnel is logged when it closes, a moment after the client has its reply.
        for _ in range(100):
            if self.log.exists():
                return [json.loads(line) for line in self.log.read_text().splitlines()]
            time.sleep(0.02)
        return []

    def test_host_outside_policy_is_blocked_and_logged(self):
        reply = self.request("CONNECT example.com:443 HTTP/1.1")
        self.assertIn("403", reply)
        self.assertEqual(self.connected, [])
        [entry] = self.entries()
        self.assertEqual(entry["host"], "example.com")
        self.assertEqual(entry["decision"], "blocked: host not in policy")

    def test_plain_http_and_other_ports_are_blocked(self):
        self.assertIn("403", self.request("GET http://api.groq.com/ HTTP/1.1"))
        self.assertIn("403", self.request("CONNECT api.groq.com:80 HTTP/1.1"))
        self.assertEqual(self.connected, [])
        self.assertEqual(len(self.entries()), 2)

    def test_allowed_host_is_tunnelled_and_logged_with_sizes_model_and_masks(self):
        reply = self.request("CONNECT api.groq.com:443 HTTP/1.1", b"hello")
        self.assertIn("200 Connection Established", reply)
        self.assertIn("echo:hello", reply)
        self.assertEqual(self.connected, [("api.groq.com", 443)])
        [entry] = self.entries()
        self.assertEqual((entry["decision"], entry["bytes_out"], entry["model"], entry["masks"]),
                         ("allowed", 5, "test-model", "gstin,bank_account"))

    def test_cut_gateway_lets_nothing_out(self):
        self.gateway.enabled = False
        self.assertIn("503", self.request("CONNECT api.groq.com:443 HTTP/1.1"))
        self.assertEqual(self.connected, [])
        self.assertEqual(self.entries()[0]["decision"], "blocked: gateway cut")


if __name__ == "__main__":
    unittest.main()
