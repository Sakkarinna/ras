import base64
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from capture_server import CaptureServerConfig, encode_file_to_base64, encode_frame_to_base64, is_authorized  # noqa: E402


class _DummyHandler:
    def __init__(self, auth_header):
        self.headers = {"Authorization": auth_header}


class CaptureServerUnitTests(unittest.TestCase):
    def test_is_authorized_checks_bearer_token(self):
        original_token = CaptureServerConfig.device_token
        CaptureServerConfig.device_token = "expected-token"
        try:
            self.assertFalse(is_authorized(_DummyHandler("")))
            self.assertFalse(is_authorized(_DummyHandler("Bearer wrong")))
            self.assertTrue(is_authorized(_DummyHandler("Bearer expected-token")))
        finally:
            CaptureServerConfig.device_token = original_token

    def test_encode_file_and_frame_to_base64_return_strings(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"abc")
            tmp_path = tmp.name
        try:
            encoded_file = encode_file_to_base64(Path(tmp_path))
            self.assertEqual(base64.b64decode(encoded_file), b"abc")
        finally:
            os.unlink(tmp_path)

        encoded_frame = encode_frame_to_base64(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertTrue(len(encoded_frame) > 10)


if __name__ == "__main__":
    unittest.main()
