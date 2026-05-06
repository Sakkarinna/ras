import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    api_base_url: str = os.getenv("FRAS_API_BASE_URL", "http://localhost:3000")
    device_code: str = os.getenv("DEVICE_CODE", "PI-CLASSROOM-001")
    device_token: str = os.getenv("DEVICE_TOKEN", "change-this-device-token")
    camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
    show_camera_preview: bool = os.getenv("SHOW_CAMERA_PREVIEW", "false").lower() == "true"
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    checkin_interval_seconds: int = int(os.getenv("CHECKIN_INTERVAL_SECONDS", "2"))
    heartbeat_interval_seconds: int = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))
    min_face_size: int = int(os.getenv("MIN_FACE_SIZE", "80"))

config = Config()
