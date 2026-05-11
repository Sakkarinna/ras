import os
import sys
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from device.health_check import check_disk_space, check_server  # noqa: E402


class DeviceReadinessSystemTests(unittest.TestCase):
    def test_device_readiness_combines_server_and_disk_checks(self):
        with patch("device.health_check.requests.get", return_value=type("Response", (), {"status_code": 200})()), patch(
            "device.health_check.shutil.disk_usage",
            return_value=type("Usage", (), {"free": 700 * 1024 * 1024})(),
        ):
            self.assertTrue(check_server("http://localhost:3000"))
            self.assertTrue(check_disk_space(min_free_mb=500))


if __name__ == "__main__":
    unittest.main()
