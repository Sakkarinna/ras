import cv2
import numpy as np


MIN_BRIGHTNESS = 35
MAX_BRIGHTNESS = 230
MIN_BLUR_SCORE = 25


def check_face_quality(frame, faces, min_face_size: int = 80) -> dict:
    if len(faces) == 0:
        return make_result(False, "Face not detected", face_detected=False, single_face=False)
    if len(faces) > 1:
        return make_result(False, "Multiple faces detected", single_face=False)

    x, y, w, h = faces[0]
    if w < min_face_size or h < min_face_size:
        return make_result(False, "Face too small")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    brightness_ok = MIN_BRIGHTNESS <= brightness <= MAX_BRIGHTNESS

    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_ok = blur_score >= MIN_BLUR_SCORE

    frame_h, frame_w = frame.shape[:2]
    face_center_x = x + (w / 2)
    face_center_y = y + (h / 2)
    centered_x = abs(face_center_x - (frame_w / 2)) <= frame_w * 0.30
    centered_y = abs(face_center_y - (frame_h / 2)) <= frame_h * 0.35
    face_centered = centered_x and centered_y

    if not brightness_ok:
        return make_result(False, "Image too dark or too bright", brightness_ok=False)
    if not blur_ok:
        return make_result(False, "Image too blurry", blur_ok=False)
    if not face_centered:
        return make_result(False, "Face not centered", face_centered=False)

    return make_result(True, "Quality check passed")

def make_result(
    passed: bool,
    message: str,
    face_detected: bool = True,
    single_face: bool = True,
    brightness_ok: bool = True,
    blur_ok: bool = True,
    face_centered: bool = True,
) -> dict:
    return {
        "faceDetected": face_detected,
        "singleFace": single_face,
        "brightnessOk": brightness_ok,
        "blurOk": blur_ok,
        "faceCentered": face_centered,
        "passed": passed,
        "message": message,
    }
