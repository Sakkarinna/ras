import os
import sys
import unittest
from unittest.mock import patch

import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.image_utils import image_to_base64, resize_face  # noqa: E402


class ImageUtilsUnitTests(unittest.TestCase):
    def test_image_to_base64_raises_when_encoding_fails(self):
        with patch("utils.image_utils.cv2.imencode", return_value=(False, None)):
            with self.assertRaises(ValueError):
                image_to_base64(np.zeros((4, 4, 3), dtype=np.uint8))

    def test_resize_face_delegates_to_cv2_resize(self):
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        resized = np.ones((224, 224, 3), dtype=np.uint8)
        with patch("utils.image_utils.cv2.resize", return_value=resized) as resize_mock:
            result = resize_face(image, (224, 224))
        resize_mock.assert_called_once()
        self.assertEqual(result.shape, (224, 224, 3))


if __name__ == "__main__":
    unittest.main()

