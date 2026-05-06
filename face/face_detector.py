from pathlib import Path
import cv2

class FaceDetector:
    def __init__(self):
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(str(cascade_path))
        if self.detector.empty():
            raise RuntimeError("Failed to load OpenCV Haar Cascade face detector")

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
        )
        return list(faces)

    def crop_face(self, frame, face_box):
        x, y, w, h = face_box
        horizontal_padding = int(w * 0.35)
        top_padding = int(h * 0.45)
        bottom_padding = int(h * 0.25)
        x1 = max(x - horizontal_padding, 0)
        y1 = max(y - top_padding, 0)
        x2 = min(x + w + horizontal_padding, frame.shape[1])
        y2 = min(y + h + bottom_padding, frame.shape[0])
        return frame[y1:y2, x1:x2]
