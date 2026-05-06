from datetime import datetime, timezone
import requests

class FrasClient:
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def get_device_by_code(self, device_code: str) -> dict:
        return self.get(f"{self.base_url}/api/devices/by-code/{device_code}")

    def get_active_session(self, device_code: str) -> dict:
        return self.get(
            f"{self.base_url}/api/attendance-sessions/active",
            params={"deviceCode": device_code},
        )

    def send_face_checkin(self, device_code: str, session_id: int, image_base64: str, quality: dict) -> dict:
        payload = {
            "deviceCode": device_code,
            "sessionId": session_id,
            "capturedAt": datetime.now(timezone.utc).isoformat(),
            "imageBase64": image_base64,
            "quality": quality,
        }
        return self.post(f"{self.base_url}/api/checkins/face", payload)

    def send_heartbeat(self, device_id: int, health: dict | None = None) -> dict:
        payload = {
            "heartbeatAt": datetime.now(timezone.utc).isoformat(),
        }
        if health:
            payload.update(health)
        return self.post(f"{self.base_url}/api/devices/{device_id}/heartbeat", payload)

    def get(self, url: str, params: dict | None = None) -> dict:
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            return self.handle_response(response)
        except requests.RequestException as error:
            return {"ok": False, "error": str(error)}

    def post(self, url: str, payload: dict) -> dict:
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            return self.handle_response(response)
        except requests.RequestException as error:
            return {"ok": False, "error": str(error)}

    def handle_response(self, response) -> dict:
        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text}
        if not response.ok:
            return {
                "ok": False,
                "statusCode": response.status_code,
                "error": data.get("error") or data.get("message") or "Request failed",
            }
        return {"ok": True, "data": data}
