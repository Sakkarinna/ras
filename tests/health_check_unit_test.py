import os
import sys
import types
import unittest
from unittest.mock import patch

import requests


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from device.health_check import check_disk_space, check_server  # noqa: E402


class HealthCheckUnitTests(unittest.TestCase):
    def test_check_server_returns_true_for_non_500_response(self):
        with patch("device.health_check.requests.get", return_value=types.SimpleNamespace(status_code=200)):
            self.assertTrue(check_server("http://localhost:3000"))

    def test_check_server_returns_false_on_request_exception(self):
        with patch("device.health_check.requests.get", side_effect=requests.RequestException("boom")):
            self.assertFalse(check_server("http://localhost:3000"))

    def test_check_disk_space_compares_free_megabytes_to_threshold(self):
        with patch("device.health_check.shutil.disk_usage", return_value=types.SimpleNamespace(free=800 * 1024 * 1024)):
            self.assertTrue(check_disk_space(min_free_mb=500))
        with patch("device.health_check.shutil.disk_usage", return_value=types.SimpleNamespace(free=100 * 1024 * 1024)):
            self.assertFalse(check_disk_space(min_free_mb=500))


if __name__ == "__main__":
    unittest.main()
