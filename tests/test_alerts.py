"""The phone alert server: local, token protected, read only. Offline tests on loopback."""
import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from relayloom.ap.alerts import AlertHub, PhoneServer


def fetch(url, method="GET"):
    request = urllib.request.Request(url, method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(request, timeout=5) as reply:
            return reply.status, reply.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


class PhoneServerTests(unittest.TestCase):
    def setUp(self):
        self.hub = AlertHub()
        self.server = PhoneServer(("127.0.0.1", 0), self.hub, token="secret-token", wait=0.3)
        self.server.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_every_request_needs_the_token(self):
        for path in ("/", "/alerts?after=0", "/?t=wrong", "/alerts?t=wrong&after=0", "/?t="):
            self.assertEqual(fetch(self.base + path)[0], 403, path)
        status, page = fetch(self.base + "/?t=secret-token")
        self.assertEqual(status, 200)
        self.assertIn("Relayloom alerts", page)
        self.assertNotIn("http://", page.replace("http://127", ""))  # the page loads nothing from anywhere else

    def test_alerts_arrive_in_order_and_only_new_ones_are_returned(self):
        self.assertEqual(json.loads(fetch(self.base + "/alerts?t=secret-token&after=0")[1]), [])
        self.hub.publish("needs_owner", "CAL-0990 needs you", "Short delivery.", "short")
        self.hub.publish("offline", "DUN-0211 held, offline", "The network is down.", "netcut-1")
        items = json.loads(fetch(self.base + "/alerts?t=secret-token&after=0")[1])
        self.assertEqual([i["id"] for i in items], [1, 2])
        self.assertEqual(items[0]["title"], "CAL-0990 needs you")
        self.assertEqual(json.loads(fetch(self.base + "/alerts?t=secret-token&after=2")[1]), [])

    def test_a_waiting_phone_gets_the_alert_as_soon_as_it_is_raised(self):
        self.server.wait = 5.0  # a phone that is waiting must be answered long before this
        threading.Timer(0.05, lambda: self.hub.publish("needs_owner", "t", "b")).start()
        started = time.perf_counter()
        items = json.loads(fetch(self.base + "/alerts?t=secret-token&after=0")[1])
        self.assertEqual(len(items), 1)
        self.assertLess(time.perf_counter() - started, 3.0)

    def test_it_is_read_only_and_serves_nothing_else(self):
        self.assertEqual(fetch(self.base + "/api/state?t=secret-token")[0], 404)
        self.assertEqual(fetch(self.base + "/api/decide?t=secret-token", "POST")[0], 405)
        self.assertEqual(fetch(self.base + "/../relayloom/ap/policy.json?t=secret-token")[0], 404)


if __name__ == "__main__":
    unittest.main()
