import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from lowcode_agent_kit.config import Config
from lowcode_agent_kit.transport import PlatformReadError, RestTransport


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "http://elsewhere.invalid/")
            self.end_headers()
            return
        if self.path == "/large":
            data = b'{"data":"' + b"x" * (1024 * 1024 + 1) + b'"}'
        else:
            data = json.dumps({
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
            }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass


class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:" + str(cls.httpd.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_auth_headers_and_query(self):
        t = RestTransport(Config(platform="eap-obpm", base_url=self.url, token="token-private"))
        response = t.request("GET", "/resource", params={"key": "采购"})
        self.assertEqual(response["authorization"], "Bearer token-private")
        self.assertIn("key=%E9%87%87%E8%B4%AD", response["path"])
        t2 = RestTransport(Config(platform="cloudfile", base_url=self.url, token="abc", auth_scheme="token"))
        self.assertEqual(t2.request("GET", "/api2/repos/")["authorization"], "Token abc")

    def test_no_redirect_or_arbitrary_url(self):
        t = RestTransport(Config(platform="extn", base_url=self.url, token="secret"))
        with self.assertRaisesRegex(PlatformReadError, "HTTP 302"):
            t.request("GET", "/redirect")
        for path in ("/../admin", "https://host.invalid/admin", "//evil", "/a?admin=true"):
            with self.assertRaises(PlatformReadError):
                t.request("GET", path)

    def test_response_size_limit(self):
        t = RestTransport(Config(platform="extn", base_url=self.url, token="secret"))
        with self.assertRaisesRegex(PlatformReadError, "1 MiB"):
            t.request("GET", "/large")


if __name__ == "__main__":
    unittest.main()
