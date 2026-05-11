import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import capture_server  # noqa: E402


class _FakeCamera:
    def read_frame(self):
        return np.zeros((16, 16, 3), dtype=np.uint8)

    def show_preview(self, frame, status_text, face_boxes=None):
        return True

    def release(self):
        return None


class _FakeWriter:
    def __init__(self, *args, **kwargs):
        self.opened = True

    def isOpened(self):
        return True

    def write(self, frame):
        return None

    def release(self):
        return None


class CaptureServerIntegrationTests(unittest.TestCase):
    def test_capture_preview_and_still_return_expected_payload_keys(self):
        with patch("capture_server.build_camera", return_value=_FakeCamera()):
            preview = capture_server.capture_preview()
            still = capture_server.capture_still()

        self.assertIn("previewImageBase64", preview)
        self.assertIn("imageBase64", still)

    def test_capture_video_returns_preview_and_video_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch("capture_server.build_camera", return_value=_FakeCamera()), patch(
            "capture_server.tempfile.mkdtemp", return_value=temp_dir
        ), patch("capture_server.cv2.VideoWriter", return_value=_FakeWriter()), patch(
            "capture_server.time.time", side_effect=[0, 0, 20]
        ), patch("capture_server.time.sleep", return_value=None):
            video_path = Path(temp_dir) / "capture.mp4"
            video_path.write_bytes(b"video")
            result = capture_server.capture_video(10)

        self.assertIn("videoBase64", result)
        self.assertEqual(result["videoName"], "capture.mp4")


if __name__ == "__main__":
    unittest.main()

