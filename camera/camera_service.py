import time

import cv2


class CameraService:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.capture = None
        self.window_name = "FRAS Camera Preview"

    def start(self) -> None:
        backends = [
            cv2.CAP_V4L2,
            cv2.CAP_ANY,
        ]

        for backend in backends:
            capture = cv2.VideoCapture(self.camera_index, backend)
            if not capture.isOpened():
                capture.release()
                continue

            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

            warmed_up = False
            for _ in range(10):
                success, frame = capture.read()
                if success and frame is not None:
                    warmed_up = True
                    break
                time.sleep(0.1)

            if warmed_up:
                self.capture = capture
                return

            capture.release()

        raise RuntimeError("Camera could not be opened")

    def read_frame(self):
        if self.capture is None:
            raise RuntimeError("Camera has not been started")
        success, frame = self.capture.read()
        if not success or frame is None:
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
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        cv2.destroyAllWindows()
