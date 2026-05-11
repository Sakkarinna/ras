import os
import sys
import unittest
from unittest.mock import patch

import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from face.quality_check import check_face_quality, make_result  # noqa: E402


class _FakeLaplacianResult:
    def __init__(self, value):
        self.value = value

    def var(self):
        return self.value


class QualityCheckUnitTests(unittest.TestCase):
    def test_make_result_contains_expected_flags(self):
        result = make_result(True, "ok")
        self.assertTrue(result["passed"])
        self.assertEqual(result["message"], "ok")

    def test_check_face_quality_rejects_missing_and_multiple_faces(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertEqual(check_face_quality(frame, [])["message"], "Face not detected")
        self.assertEqual(check_face_quality(frame, [(1, 1, 90, 90), (5, 5, 80, 80)])["message"], "Multiple faces detected")

    def test_check_face_quality_accepts_single_clear_centered_face(self):
        frame = np.full((200, 200, 3), 120, dtype=np.uint8)
        faces = [(60, 50, 90, 90)]
        with patch("face.quality_check.cv2.cvtColor", return_value=np.full((200, 200), 120, dtype=np.uint8)), patch(
            "face.quality_check.cv2.Laplacian", return_value=_FakeLaplacianResult(25)
        ):
            result = check_face_quality(frame, faces)
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()

