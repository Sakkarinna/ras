import os
import sys
import time
import unittest
from unittest.mock import patch

import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from face.quality_check import check_face_quality  # noqa: E402


class _FakeLaplacianResult:
    def var(self):
        return 25


class QualityPipelineLoadStressTests(unittest.TestCase):
    def test_quality_check_stays_responsive_under_repeated_face_validation(self):
        frame = np.full((200, 200, 3), 120, dtype=np.uint8)
        faces = [(60, 50, 90, 90)]
        with patch("face.quality_check.cv2.cvtColor", return_value=np.full((200, 200), 120, dtype=np.uint8)), patch(
            "face.quality_check.cv2.Laplacian", return_value=_FakeLaplacianResult()
        ):
            started_at = time.perf_counter()
            for _ in range(200):
                result = check_face_quality(frame, faces)
            elapsed = time.perf_counter() - started_at

        self.assertTrue(result["passed"])
        self.assertLess(elapsed, 0.5)


if __name__ == "__main__":
    unittest.main()

