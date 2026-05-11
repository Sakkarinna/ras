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
    camera_width: int = int(os.getenv("CAMERA_WIDTH", "1280"))
    camera_height: int = int(os.getenv("CAMERA_HEIGHT", "720"))
    camera_pixel_format: str = os.getenv("CAMERA_PIXEL_FORMAT", "RGB888").strip().upper()
    camera_capture_array_order: str = os.getenv("CAMERA_CAPTURE_ARRAY_ORDER", "BGR").strip().upper()
    autofocus_enabled: bool = os.getenv("CAMERA_AUTOFOCUS_ENABLED", "true").lower() == "true"
    autofocus_mode: str = os.getenv("CAMERA_AUTOFOCUS_MODE", "continuous").strip().lower()
    autofocus_speed: str = os.getenv("CAMERA_AUTOFOCUS_SPEED", "fast").strip().lower()
    autofocus_warmup_seconds: float = float(os.getenv("CAMERA_AUTOFOCUS_WARMUP_SECONDS", "1.2"))
    show_camera_preview: bool = os.getenv("SHOW_CAMERA_PREVIEW", "false").lower() == "true"
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    checkin_interval_seconds: int = int(os.getenv("CHECKIN_INTERVAL_SECONDS", "2"))
    heartbeat_interval_seconds: int = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))
    frame_loop_delay_seconds: float = float(os.getenv("FRAME_LOOP_DELAY_SECONDS", "0.05"))
    submit_cooldown_seconds: float = float(os.getenv("SUBMIT_COOLDOWN_SECONDS", "2"))
    min_face_size: int = int(os.getenv("MIN_FACE_SIZE", "80"))

config = Config()
