import argparse
import time
from datetime import datetime
from pathlib import Path

import cv2

from camera.camera_service import CameraService
from config import config
from face.face_detector import FaceDetector
from face.quality_check import check_face_quality
from utils.image_utils import resize_face
from utils.logger import setup_logger


logger = setup_logger("fras-manual-capture")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture cropped face images on Raspberry Pi using the FRAS camera logic."
    )
    parser.add_argument(
        "--output-dir",
        default="captures/manual_faces",
        help="Base directory for saved face images.",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=1.5,
        help="Minimum seconds between saved images.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Maximum number of images to save. Use 0 for unlimited.",
    )
    parser.add_argument(
        "--no-quality-check",
        action="store_true",
        help="Save the largest detected face without running the local quality gate.",
    )
    return parser.parse_args()


def make_capture_dir(base_dir: str) -> Path:
    session_dir = Path(base_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def choose_primary_face(faces: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    return max(faces, key=lambda face: face[2] * face[3])


def save_face_image(output_dir: Path, image_index: int, face_crop) -> Path:
    file_path = output_dir / f"face_{image_index:03d}.jpg"
    success = cv2.imwrite(str(file_path), face_crop)
    if not success:
        raise RuntimeError(f"Failed to save image to {file_path}")
    return file_path


def main() -> None:
    args = parse_args()
    output_dir = make_capture_dir(args.output_dir)
    camera = CameraService(config.camera_index)
    face_detector = FaceDetector()
    saved_images = 0
    last_saved_at = 0.0

    logger.info("Saving cropped faces to %s", output_dir)

    try:
        camera.start()
        logger.info("Camera started successfully")

        while True:
            try:
                frame = camera.read_frame()
            except RuntimeError as error:
                logger.warning("Camera read failed: %s", error)
                time.sleep(config.frame_loop_delay_seconds)
                continue

            faces = face_detector.detect_faces(frame)
            quality = check_face_quality(frame, faces, config.min_face_size)

            if not faces:
                preview_status = "Waiting for face"
            elif len(faces) > 1:
                preview_status = "Multiple faces detected"
            else:
                preview_status = quality["message"]

            should_continue = camera.show_preview(frame, preview_status, face_boxes=faces)
            if not should_continue:
                logger.info("Camera preview closed by user")
                break

            if not faces:
                time.sleep(config.frame_loop_delay_seconds)
                continue

            now = time.monotonic()
            if now - last_saved_at < args.cooldown:
                time.sleep(config.frame_loop_delay_seconds)
                continue

            if not args.no_quality_check and not quality["passed"]:
                logger.info("Skipped capture: %s", quality["message"])
                time.sleep(config.frame_loop_delay_seconds)
                continue

            primary_face = choose_primary_face(faces)
            face_crop = face_detector.crop_face(frame, primary_face)
            face_crop = resize_face(face_crop, (320, 320))

            saved_images += 1
            saved_path = save_face_image(output_dir, saved_images, face_crop)
            last_saved_at = now
            logger.info("Saved face image %s", saved_path)

            if args.max_images > 0 and saved_images >= args.max_images:
                logger.info("Reached max image limit (%s)", args.max_images)
                break

            time.sleep(config.frame_loop_delay_seconds)

    except KeyboardInterrupt:
        logger.info("Stopped by user")
    finally:
        camera.release()
        logger.info("Camera released")


if __name__ == "__main__":
    main()
