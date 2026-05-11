import os
import sys
import unittest

import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main import show_preview_frame  # noqa: E402


class _FakeCamera:
    def __init__(self, frame=None, error=None):
        self.frame = frame
        self.error = error

    def read_frame(self):
        if self.error:
            raise self.error
        return self.frame

    def show_preview(self, frame, status_text, face_boxes=None):
        return bool(face_boxes)


class _FakeFaceDetector:
    def __init__(self, faces):
        self.faces = faces

    def detect_faces(self, frame):
        return self.faces


class MainIntegrationTests(unittest.TestCase):
    def test_show_preview_frame_returns_true_when_camera_read_fails(self):
        camera = _FakeCamera(error=RuntimeError("camera failed"))
        detector = _FakeFaceDetector([])
        self.assertTrue(show_preview_frame(camera, detector, "Waiting"))

    def test_show_preview_frame_uses_detected_faces_in_preview(self):
        camera = _FakeCamera(frame=np.zeros((10, 10, 3), dtype=np.uint8))
        detector = _FakeFaceDetector([(1, 1, 5, 5)])
        self.assertTrue(show_preview_frame(camera, detector, "Ready"))


if __name__ == "__main__":
    unittest.main()

