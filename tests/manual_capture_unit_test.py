import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from manual_capture import choose_primary_face, make_capture_dir, save_face_image  # noqa: E402


class ManualCaptureUnitTests(unittest.TestCase):
    def test_choose_primary_face_uses_largest_area(self):
        self.assertEqual(choose_primary_face([(0, 0, 10, 10), (0, 0, 20, 20)]), (0, 0, 20, 20))

    def test_make_capture_dir_creates_timestamped_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = make_capture_dir(temp_dir)
            self.assertTrue(result.exists())
            self.assertTrue(result.is_dir())

    def test_save_face_image_writes_named_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            with patch("manual_capture.cv2.imwrite", return_value=True):
                saved = save_face_image(output_dir, 1, np.zeros((10, 10, 3), dtype=np.uint8))
            self.assertEqual(saved.name, "face_001.jpg")


if __name__ == "__main__":
    unittest.main()

