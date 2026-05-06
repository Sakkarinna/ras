import base64
import cv2

def image_to_base64(image) -> str:
    success, buffer = cv2.imencode(".jpg", image)
    if not success:
        raise ValueError("Failed to encode image")
    return base64.b64encode(buffer).decode("utf-8")

def resize_face(image, size=(224, 224)):
    return cv2.resize(image, size)
