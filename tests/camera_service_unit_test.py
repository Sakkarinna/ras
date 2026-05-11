import os
import sys
import types
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import camera.camera_service as camera_service_module  # noqa: E402
from camera.camera_service import CameraService  # noqa: E402


class CameraServiceUnitTests(unittest.TestCase):
    def test_fallback_af_mode_values_work_without_libcamera(self):
        service = CameraService()
        original_controls = camera_service_module.libcamera_controls
        camera_service_module.libcamera_controls = None
        try:
            self.assertEqual(service._get_af_mode_value("continuous"), 2)
            self.assertEqual(service._get_af_mode_value("auto"), 1)
            self.assertEqual(service._get_af_trigger_value(), 0)
            self.assertIsNone(service._get_af_speed_value())
        finally:
            camera_service_module.libcamera_controls = original_controls

    def test_libcamera_enums_are_used_when_available(self):
        service = CameraService()
        original_controls = camera_service_module.libcamera_controls
        camera_service_module.libcamera_controls = types.SimpleNamespace(
            AfModeEnum=types.SimpleNamespace(Continuous=11, Auto=12),
            AfTriggerEnum=types.SimpleNamespace(Start=13),
            AfSpeedEnum=types.SimpleNamespace(Fast=14, Normal=15),
        )
        try:
            self.assertEqual(service._get_af_mode_value("continuous"), 11)
            self.assertEqual(service._get_af_trigger_value(), 13)
            self.assertEqual(service._get_af_speed_value(), 14)
        finally:
            camera_service_module.libcamera_controls = original_controls


if __name__ == "__main__":
    unittest.main()

