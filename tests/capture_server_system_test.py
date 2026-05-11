import io
import json
import os
import sys
import unittest
from http import HTTPStatus


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from capture_server import CaptureHandler  # noqa: E402


class CaptureServerSystemTests(unittest.TestCase):
    def make_handler(self, path="/capture", payload=None, auth="Bearer change-this-device-token"):
        handler = CaptureHandler.__new__(CaptureHandler)
        raw = json.dumps(payload or {}).encode("utf-8")
        handler.path = path
        handler.headers = {"Content-Length": str(len(raw)), "Authorization": auth}
        handler.rfile = io.BytesIO(raw)
        handler.wfile = io.BytesIO()
        handler.responses = []
        handler.send_response = lambda code: handler.responses.append(code)
        handler.send_header = lambda *args, **kwargs: None
        handler.end_headers = lambda: None
        return handler

    def test_health_endpoint_returns_ok(self):
        handler = self.make_handler(path="/health")
        handler.do_GET()
        self.assertEqual(handler.responses[0], HTTPStatus.OK.value)

    def test_invalid_capture_type_returns_bad_request(self):
        handler = self.make_handler(payload={"captureType": "unknown"})
        handler.do_POST()
        self.assertEqual(handler.responses[0], HTTPStatus.BAD_REQUEST.value)


if __name__ == "__main__":
    unittest.main()

