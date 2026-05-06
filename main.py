import time

from api.fras_client import FrasClient
from camera.camera_service import CameraService
from config import config
from device.feedback import show_error, show_idle, show_success, show_warning
from face.face_detector import FaceDetector
from face.quality_check import check_face_quality
from utils.image_utils import image_to_base64, resize_face
from utils.logger import setup_logger

logger = setup_logger()


def main() -> None:
    logger.info("Starting FRAS Raspberry Pi device")

    camera = CameraService(config.camera_index)
    face_detector = FaceDetector()
    client = FrasClient(config.api_base_url, config.device_token, config.request_timeout)

    try:
        camera.start()
        logger.info("Camera started successfully")

        device_response = client.get_device_by_code(config.device_code)
        if device_response["ok"]:
            logger.info("Device verified by server")
            device_payload = device_response["data"].get("data", device_response["data"])
            device_id = device_payload.get("deviceId") or device_payload.get("device_id")
            if device_id:
                client.send_heartbeat(int(device_id))
        else:
            logger.warning("Device verification failed: %s", device_response["error"])

        while True:
            session_response = client.get_active_session(config.device_code)

            if not session_response["ok"]:
                show_warning("Server unavailable or no active session")
                logger.warning("Active session check failed: %s", session_response["error"])
                time.sleep(config.checkin_interval_seconds)
                continue

            session_data = session_response["data"].get("data", session_response["data"])
            session_id = session_data.get("sessionId") or session_data.get("session_id") or session_data.get("id")

            if not session_id:
                show_idle("No active attendance session")
                time.sleep(config.checkin_interval_seconds)
                continue

            frame = camera.read_frame()
            faces = face_detector.detect_faces(frame)

            quality = check_face_quality(frame, faces, config.min_face_size)
            if not quality["passed"]:
                show_warning(quality["message"])
                logger.info("Quality failed: %s", quality["message"])
                time.sleep(config.checkin_interval_seconds)
                continue

            face_crop = face_detector.crop_face(frame, faces[0])
            face_crop = resize_face(face_crop, (224, 224))
            image_base64 = image_to_base64(face_crop)

            response = client.send_face_checkin(
                config.device_code,
                int(session_id),
                image_base64,
                quality,
            )

            if not response["ok"]:
                show_error("Check-in failed")
                logger.error("Check-in failed: %s", response["error"])
                time.sleep(config.checkin_interval_seconds)
                continue

            result = response["data"].get("data", response["data"])
            status = result.get("status")
            message = result.get("message", "Check-in processed")

            if status == "recognized":
                student_name = result.get("studentName", "Student")
                attendance_status = result.get("attendanceStatus", "")
                show_success(f"{student_name}: {attendance_status}")
            elif status == "duplicate":
                show_warning("Already checked in")
            elif status == "unknown":
                show_warning("Face not recognized")
            elif status == "no_active_session":
                show_idle("No active session")
            else:
                show_idle(message)

            logger.info("Server result: %s", result)
            time.sleep(config.checkin_interval_seconds)

    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as error:
        show_error(str(error))
        logger.exception("Unexpected error")
    finally:
        camera.release()
        logger.info("Camera released")


if __name__ == "__main__":
    main()
