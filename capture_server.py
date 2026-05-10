from __future__ import annotations

import argparse
import base64
import json
import tempfile
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2

from camera.camera_service import CameraService
from config import config


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


def capture_preview() -> dict:
    camera = build_camera()
    try:
        frame = camera.read_frame()
        camera.show_preview(frame, "Preview face")
        return {
            "previewImageBase64": encode_frame_to_base64(frame),
            "previewImageName": "preview.jpg",
        }
    finally:
        camera.release()


def capture_still() -> dict:
    camera = build_camera()
    try:
        frame = camera.read_frame()
        camera.show_preview(frame, "Capture still")
        encoded = encode_frame_to_base64(frame)
        return {
            "previewImageBase64": encoded,
            "previewImageName": "preview.jpg",
            "imageBase64": encoded,
            "imageName": "photo.jpg",
        }
    finally:
        camera.release()


def capture_video(duration_seconds: int = 10) -> dict:
    camera = build_camera()
    temp_dir = Path(tempfile.mkdtemp(prefix="fras-pi-capture-"))
    video_path = temp_dir / "capture.mp4"
    writer = None
    preview_base64 = None
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
            if preview_base64 is None:
                preview_base64 = encode_frame_to_base64(frame)
            writer.write(frame)
            camera.show_preview(frame, "Recording 10s video")
            time.sleep(0.02)
            frame = camera.read_frame()

        writer.release()
        writer = None
        return {
            "previewImageBase64": preview_base64,
            "previewImageName": "preview.jpg",
            "videoBase64": encode_file_to_base64(video_path),
            "videoName": "capture.mp4",
        }
    finally:
        camera.release()
        if writer is not None:
            writer.release()
        try:
            if video_path.exists():
                video_path.unlink()
            temp_dir.rmdir()
        except OSError:
            pass


class CaptureHandler(BaseHTTPRequestHandler):
    server_version = "FRAS-PI-CAPTURE/1.0"

    def do_GET(self) -> None:
        if self.path == "/health":
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
            if capture_type == "PREVIEW":
                result = capture_preview()
            elif capture_type == "STILL":
                result = capture_still()
            elif capture_type == "VIDEO":
                result = capture_video(10)
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid capture type"})
                return

            self._send_json(HTTPStatus.OK, {"data": result})
        except Exception as error:
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

    server = ThreadingHTTPServer((CaptureServerConfig.host, CaptureServerConfig.port), CaptureHandler)
    print(
        f"FRAS Raspberry Pi capture server listening on "
        f"http://{CaptureServerConfig.host}:{CaptureServerConfig.port}"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
