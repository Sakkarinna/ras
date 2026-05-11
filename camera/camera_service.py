import time

import cv2
from config import config

try:
    from picamera2 import Picamera2
except ImportError:  # pragma: no cover - only happens on non-Pi setups
    Picamera2 = None

try:
    from libcamera import controls as libcamera_controls
except ImportError:  # pragma: no cover - only happens on non-Pi setups
    libcamera_controls = None


class CameraService:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.camera = None
        self.window_name = "FRAS Camera Preview"

    def start(self) -> None:
        if Picamera2 is None:
            raise RuntimeError(
                "Picamera2 is not installed. Run 'sudo apt install -y python3-picamera2' and recreate the venv with --system-site-packages."
            )

        try:
            camera = Picamera2(camera_num=self.camera_index)
            configuration = camera.create_video_configuration(
                main={"size": (config.camera_width, config.camera_height), "format": "BGR888"}
            )
            camera.configure(configuration)
            camera.start()
            self._configure_autofocus(camera)

            warmed_up = False
            for _ in range(20):
                frame = camera.capture_array()
                if frame is not None and getattr(frame, "size", 0) > 0:
                    warmed_up = True
                    break
                time.sleep(0.1)

            if not warmed_up:
                camera.stop()
                camera.close()
                raise RuntimeError("Camera opened but no frames were received")

            self.camera = camera
        except Exception as error:
            raise RuntimeError("Camera could not be opened") from error

    def _configure_autofocus(self, camera) -> None:
        if not config.autofocus_enabled:
            return

        autofocus_mode = config.autofocus_mode
        controls = {}

        # Camera Module 3 supports autofocus through libcamera controls.
        # Keep this guarded so non-autofocus camera modules still work.
        if autofocus_mode == "continuous":
            controls["AfMode"] = self._get_af_mode_value("continuous")
        elif autofocus_mode == "auto":
            controls["AfMode"] = self._get_af_mode_value("auto")
            controls["AfTrigger"] = self._get_af_trigger_value()
        else:
            return

        autofocus_speed = self._get_af_speed_value()
        if autofocus_speed is not None:
            controls["AfSpeed"] = autofocus_speed

        try:
            camera.set_controls(controls)
            if config.autofocus_warmup_seconds > 0:
                time.sleep(config.autofocus_warmup_seconds)
        except Exception:
            return

    def _get_af_mode_value(self, autofocus_mode: str):
        if libcamera_controls is not None:
            if autofocus_mode == "continuous":
                return libcamera_controls.AfModeEnum.Continuous
            if autofocus_mode == "auto":
                return libcamera_controls.AfModeEnum.Auto
        if autofocus_mode == "continuous":
            return 2
        return 1

    def _get_af_trigger_value(self):
        if libcamera_controls is not None:
            return libcamera_controls.AfTriggerEnum.Start
        return 0

    def _get_af_speed_value(self):
        if libcamera_controls is None:
            return None
        if config.autofocus_speed == "normal":
            return libcamera_controls.AfSpeedEnum.Normal
        return libcamera_controls.AfSpeedEnum.Fast

    def read_frame(self):
        if self.camera is None:
            raise RuntimeError("Camera has not been started")

        frame = self.camera.capture_array()
        if frame is None or getattr(frame, "size", 0) == 0:
            raise RuntimeError("Could not read frame from camera")

        return frame

    def show_preview(self, frame, status_text: str = "", face_boxes=None) -> bool:
        preview_frame = frame.copy()
        if face_boxes:
            for x, y, w, h in face_boxes:
                cv2.rectangle(preview_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if status_text:
            cv2.putText(
                preview_frame,
                status_text,
                (16, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
        cv2.imshow(self.window_name, preview_frame)
        key = cv2.waitKey(1) & 0xFF
        return key not in (27, ord("q"), ord("Q"))

    def release(self) -> None:
        if self.camera is not None:
            try:
                self.camera.stop()
            finally:
                self.camera.close()
                self.camera = None
        cv2.destroyAllWindows()
