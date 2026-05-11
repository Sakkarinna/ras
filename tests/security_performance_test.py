import os
import sys
import unittest
from unittest.mock import patch

import requests


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from capture_server import CaptureServerConfig, is_authorized  # noqa: E402
from device.health_check import check_server  # noqa: E402


class _DummyHandler:
    def __init__(self, auth_header):
        self.headers = {"Authorization": auth_header}


class RaspberryPiSecurityPerformanceTests(unittest.TestCase):
    def test_capture_server_authorization_rejects_wrong_token(self):
        original_token = CaptureServerConfig.device_token
        CaptureServerConfig.device_token = "expected-token"
        try:
            self.assertFalse(is_authorized(_DummyHandler("Bearer wrong")))
            self.assertTrue(is_authorized(_DummyHandler("Bearer expected-token")))
        finally:
            CaptureServerConfig.device_token = original_token

    def test_server_check_fails_closed_on_request_error(self):
        with patch("device.health_check.requests.get", side_effect=requests.RequestException("network down")):
            self.assertFalse(check_server("http://localhost:3000"))


if __name__ == "__main__":
    unittest.main()
