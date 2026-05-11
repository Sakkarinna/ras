import base64
from io import BytesIO

import cv2
from PIL import Image

def image_to_base64(image) -> str:
    # Keep OpenCV processing in BGR, then convert to RGB for the server-bound image payload.
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rgb_pil_image = Image.fromarray(rgb_image)
    buffer = BytesIO()
    rgb_pil_image.save(buffer, format="JPEG")
    encoded = buffer.getvalue()
    if not encoded:
        raise ValueError("Failed to encode image")
    return base64.b64encode(encoded).decode("utf-8")

def resize_face(image, size=(224, 224)):
    return cv2.resize(image, size)
