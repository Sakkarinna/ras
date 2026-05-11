from __future__ import annotations

import argparse
import base64
import json
import tempfile
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socket import AF_INET, SOCK_DGRAM, socket
from urllib.parse import urlparse

import cv2

from api.fras_client import FrasClient
from camera.camera_service import CameraService
from config import config
from device.health_check import check_disk_space, check_server
from utils.logger import setup_logger


logger = setup_logger("fras-capture-server")


def encode_frame_to_base64(frame) -> str:
    success, encoded = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Failed to encode captured frame.")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


def encode_file_to_base64(file_path: Path) -> str:
    return base64.b64encode(file_path.read_bytes()).decode("utf-8")


class CaptureServerConfig:
    host = "0.0.0.0"
    port = 8002
    device_token = config.device_token
    camera_index = config.camera_index
    api_base_url = config.api_base_url
    device_code = config.device_code
    request_timeout = config.request_timeout
    checkin_interval_seconds = config.checkin_interval_seconds
    heartbeat_interval_seconds = config.heartbeat_interval_seconds


CAMERA_LOCK = threading.Lock()
DEVICE_ID: int | None = None
DEVICE_IP_ADDRESS: str | None = None
LAST_HEARTBEAT = 0.0
ACTIVE_CAMERA: CameraService | None = None
PREVIEW_THREAD: threading.Thread | None = None
PREVIEW_STOP_EVENT = threading.Event()
PREVIEW_STATUS_TEXT = "Camera ready"


def get_client() -> FrasClient:
    return FrasClient(
        CaptureServerConfig.api_base_url,
        CaptureServerConfig.device_token,
        CaptureServerConfig.request_timeout,
    )


def resolve_local_ip(api_base_url: str) -> str | None:
    parsed = urlparse(api_base_url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return None

    try:
        with socket(AF_INET, SOCK_DGRAM) as sock:
            sock.connect((host, port))
            return sock.getsockname()[0]
    except OSError:
        return None


def is_authorized(handler: BaseHTTPRequestHandler) -> bool:
    authorization = handler.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return False
    token = authorization[len("Bearer "):].strip()
    return token == CaptureServerConfig.device_token


def build_camera() -> CameraService:
    camera = CameraService(CaptureServerConfig.camera_index)
    camera.start()
    return camera


def get_active_camera() -> CameraService:
    global ACTIVE_CAMERA

    if ACTIVE_CAMERA is None:
        ACTIVE_CAMERA = build_camera()
    return ACTIVE_CAMERA


def close_active_camera() -> None:
    global ACTIVE_CAMERA

    if ACTIVE_CAMERA is not None:
        ACTIVE_CAMERA.release()
        ACTIVE_CAMERA = None


def _preview_loop() -> None:
    while not PREVIEW_STOP_EVENT.is_set():
        try:
            with CAMERA_LOCK:
                if ACTIVE_CAMERA is None:
                    break
                frame = ACTIVE_CAMERA.read_frame()
                ACTIVE_CAMERA.show_preview(frame, PREVIEW_STATUS_TEXT)
            time.sleep(0.03)
        except Exception as error:
            logger.warning("Live preview update failed: %s", error)
            time.sleep(0.1)


def start_preview_loop(status_text: str = "Camera ready") -> None:
    global PREVIEW_THREAD
    global PREVIEW_STATUS_TEXT

    PREVIEW_STATUS_TEXT = status_text
    if PREVIEW_THREAD is not None and PREVIEW_THREAD.is_alive():
        return

    PREVIEW_STOP_EVENT.clear()
    PREVIEW_THREAD = threading.Thread(target=_preview_loop, daemon=True)
    PREVIEW_THREAD.start()


def stop_preview_loop() -> None:
    global PREVIEW_THREAD

    PREVIEW_STOP_EVENT.set()
    if PREVIEW_THREAD is not None and PREVIEW_THREAD.is_alive():
        PREVIEW_THREAD.join(timeout=1.0)
    PREVIEW_THREAD = None


def with_camera(action, *, keep_open: bool = False):
    with CAMERA_LOCK:
        camera = get_active_camera() if keep_open else build_camera()
        try:
            return action(camera)
        finally:
            if not keep_open:
                camera.release()


def open_camera() -> dict:
    with_camera(lambda _camera: {"cameraOpen": True}, keep_open=True)
    start_preview_loop("Camera ready")
    return {"cameraOpen": True}


def close_camera() -> dict:
    stop_preview_loop()
    with CAMERA_LOCK:
        close_active_camera()
    return {"cameraOpen": False}


def capture_preview() -> dict:
    def action(camera: CameraService) -> dict:
        frame = camera.read_frame()
        camera.show_preview(frame, "Preview face")
        return {
            "previewImageBase64": encode_frame_to_base64(frame),
            "previewImageName": "preview.jpg",
        }

    return with_camera(action, keep_open=True)


def capture_still() -> dict:
    def action(camera: CameraService) -> dict:
        frame = camera.read_frame()
        camera.show_preview(frame, "Capture still")
        encoded = encode_frame_to_base64(frame)
        return {
            "imageBase64": encoded,
            "imageName": "photo.jpg",
        }

    return with_camera(action, keep_open=True)


def capture_video(duration_seconds: int = 10) -> dict:
    def action(camera: CameraService) -> dict:
        temp_dir = Path(tempfile.mkdtemp(prefix="fras-pi-capture-"))
        video_path = temp_dir / "capture.mp4"
        writer = None
        try:
            first_frame = camera.read_frame()
            height, width = first_frame.shape[:2]
            fps = 20.0
            writer = cv2.VideoWriter(
                str(video_path),
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height),
            )
            if not writer.isOpened():
                raise RuntimeError("Unable to initialize video writer.")

            start = time.time()
            frame = first_frame
            while time.time() - start < duration_seconds:
                writer.write(frame)
                camera.show_preview(frame, "Recording 10s video")
                time.sleep(0.02)
                frame = camera.read_frame()

            writer.release()
            writer = None
            return {
                "videoBase64": encode_file_to_base64(video_path),
                "videoName": "capture.mp4",
            }
        finally:
            if writer is not None:
                writer.release()
            try:
                if video_path.exists():
                    video_path.unlink()
                temp_dir.rmdir()
            except OSError:
                pass

    return with_camera(action, keep_open=True)


def ensure_registered() -> int | None:
    global DEVICE_ID
    global DEVICE_IP_ADDRESS

    if DEVICE_IP_ADDRESS is None:
        DEVICE_IP_ADDRESS = resolve_local_ip(CaptureServerConfig.api_base_url)

    response = get_client().register_device(CaptureServerConfig.device_code, DEVICE_IP_ADDRESS)
    if not response["ok"]:
        logger.warning("Device registration failed: %s", response["error"])
        return DEVICE_ID

    payload = response["data"].get("data", response["data"])
    DEVICE_ID = payload.get("deviceId") or payload.get("device_id")
    return int(DEVICE_ID) if DEVICE_ID is not None else None


def build_health_payload(camera_ready: bool) -> dict:
    health = {
        "cameraReady": camera_ready,
        "diskOk": check_disk_space(),
        "serverReachable": check_server(CaptureServerConfig.api_base_url, CaptureServerConfig.request_timeout),
        "issueSummary": None,
    }
    if not camera_ready:
        health["issueSummary"] = "Camera unavailable on Raspberry Pi"
    elif not health["diskOk"]:
        health["issueSummary"] = "Low disk space on Raspberry Pi"
    if DEVICE_IP_ADDRESS:
        health["ipAddress"] = DEVICE_IP_ADDRESS
    return health


def probe_camera_ready() -> bool:
    try:
        def action(camera: CameraService) -> bool:
            frame = camera.read_frame()
            return frame is not None and getattr(frame, "size", 0) > 0

        return bool(with_camera(action, keep_open=ACTIVE_CAMERA is not None))
    except Exception as error:
        logger.warning("Camera probe failed: %s", error)
        return False


def send_capture_server_heartbeat(force: bool = False) -> None:
    global LAST_HEARTBEAT

    device_id = ensure_registered()
    if not device_id:
        return

    now = time.monotonic()
    if not force and now - LAST_HEARTBEAT < CaptureServerConfig.heartbeat_interval_seconds:
        return

    camera_ready = probe_camera_ready()
    health = build_health_payload(camera_ready)

    heartbeat = get_client().send_heartbeat(int(device_id), health)
    if not heartbeat["ok"]:
        logger.warning("Capture server heartbeat failed: %s", heartbeat["error"])
    LAST_HEARTBEAT = now


def heartbeat_loop() -> None:
    while True:
        try:
            send_capture_server_heartbeat()
        except Exception:
            logger.exception("Unexpected capture server heartbeat error")
        time.sleep(CaptureServerConfig.checkin_interval_seconds)


class CaptureHandler(BaseHTTPRequestHandler):
    server_version = "FRAS-PI-CAPTURE/1.0"

    def do_GET(self) -> None:
        if self.path == "/health":
            try:
                send_capture_server_heartbeat(force=True)
            except Exception:
                logger.exception("Health-triggered heartbeat failed")
            self._send_json(HTTPStatus.OK, {"data": {"status": "ok"}})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        if not is_authorized(self):
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"})
            return

        if self.path != "/capture":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        try:
            payload = self._read_json()
            capture_type = str(payload.get("captureType", "")).strip().upper()
            if capture_type == "OPEN":
                result = open_camera()
            elif capture_type == "CLOSE":
                result = close_camera()
            elif capture_type == "PREVIEW":
                result = capture_preview()
            elif capture_type == "STILL":
                result = capture_still()
            elif capture_type == "VIDEO":
                result = capture_video(10)
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid capture type"})
                return

            try:
                send_capture_server_heartbeat(force=True)
            except Exception:
                logger.exception("Post-capture heartbeat failed")

            self._send_json(HTTPStatus.OK, {"data": result})
        except Exception as error:
            try:
                send_capture_server_heartbeat(force=True)
            except Exception:
                logger.exception("Failure heartbeat after capture error failed")
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(content_length)
        return json.loads(payload.decode("utf-8")) if payload else {}

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FRAS Raspberry Pi direct capture server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--camera-index", type=int, default=config.camera_index)
    parser.add_argument("--device-token", default=config.device_token)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    CaptureServerConfig.host = args.host
    CaptureServerConfig.port = args.port
    CaptureServerConfig.camera_index = args.camera_index
    CaptureServerConfig.device_token = args.device_token

    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    server = ThreadingHTTPServer((CaptureServerConfig.host, CaptureServerConfig.port), CaptureHandler)
    print(
        f"FRAS Raspberry Pi capture server listening on "
        f"http://{CaptureServerConfig.host}:{CaptureServerConfig.port}"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
