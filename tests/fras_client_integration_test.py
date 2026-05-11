import os
import sys
import types
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.fras_client import FrasClient  # noqa: E402


class FrasClientIntegrationTests(unittest.TestCase):
    def test_get_and_post_wrap_successful_responses(self):
        client = FrasClient("http://localhost:3000", "token")
        response = types.SimpleNamespace(ok=True, json=lambda: {"data": {"deviceId": 1}})
        with patch("api.fras_client.requests.get", return_value=response), patch("api.fras_client.requests.post", return_value=response):
            self.assertTrue(client.get_device_by_code("PI-001")["ok"])
            self.assertTrue(client.send_heartbeat(1)["ok"])

    def test_handle_response_returns_error_payload_for_failed_requests(self):
        client = FrasClient("http://localhost:3000", "token")
        response = types.SimpleNamespace(ok=False, status_code=404, json=lambda: {"error": "Not found"})
        result = client.handle_response(response)
        self.assertFalse(result["ok"])
        self.assertEqual(result["statusCode"], 404)


if __name__ == "__main__":
    unittest.main()

