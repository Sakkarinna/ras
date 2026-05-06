import time

import cv2

try:
    from picamera2 import Picamera2
except ImportError:  # pragma: no cover - only happens on non-Pi setups
    Picamera2 = None


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
            configuration = camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            camera.configure(configuration)
            camera.start()

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

    def read_frame(self):
        if self.camera is None:
            raise RuntimeError("Camera has not been started")

        frame = self.camera.capture_array()
        if frame is None or getattr(frame, "size", 0) == 0:
            raise RuntimeError("Could not read frame from camera")

        # Picamera2 returns RGB arrays; OpenCV processing in this app expects BGR.
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

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
