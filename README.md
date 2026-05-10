# FRAS Raspberry Pi Starter Code

This is a simple Raspberry Pi edge-device prototype for the Face Recognition Attendance System.

## What it does

1. Opens the Raspberry Pi camera.
2. Checks if there is an active attendance session.
3. Captures a frame.
4. Detects one face.
5. Checks basic image quality.
6. Crops the face.
7. Converts the cropped face to Base64.
8. Sends the check-in request to the FRAS server.
9. Shows simple console feedback.

The Raspberry Pi does not store biometric embeddings and does not permanently store raw face images.

## Install

```bash
sudo apt update
sudo apt install -y python3-picamera2
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

`Picamera2` is installed from Raspberry Pi OS packages, not from `pip`. The `--system-site-packages` flag lets the virtual environment use that system-installed camera library.

## Camera Module 3 Autofocus Setup

This project now enables Camera Module 3 autofocus through the shared `CameraService`, so all of these commands:

- `python main.py`
- `python capture_server.py`
- `python manual_capture.py`

use the same autofocus behavior automatically.

Recommended `.env` values for Camera Module 3:

```txt
CAMERA_INDEX=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_AUTOFOCUS_ENABLED=true
CAMERA_AUTOFOCUS_MODE=continuous
CAMERA_AUTOFOCUS_SPEED=fast
CAMERA_AUTOFOCUS_WARMUP_SECONDS=1.2
```

Mode notes:

- `continuous`: keeps autofocus adjusting while the camera is running
- `auto`: triggers autofocus during startup, then continues with the captured stream
- `fast`: tries to lock focus more aggressively, which is usually better for live FRAS use
- `normal`: slower focus adjustments if `fast` becomes unstable on your Pi

If autofocus causes issues on a different camera module, disable it with:

```txt
CAMERA_AUTOFOCUS_ENABLED=false
```

## Direct Pi Capture Server

For admin face enrollment preview/photo/video from `web_app`, run this separate Pi command:

```bash
python capture_server.py
```

Or with explicit options:

```bash
python capture_server.py --host 0.0.0.0 --port 8002 --camera-index 0 --device-token change-this-device-token
```

This is separate from `main.py`. It only handles direct camera capture requests from `web_app`.

## Recommended Setup Flow on Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3-picamera2
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and make sure at least these values are correct:

```txt
FRAS_API_BASE_URL=http://YOUR_WEB_APP_HOST:3000
DEVICE_CODE=PI-CLASSROOM-001
DEVICE_TOKEN=change-this-device-token
CAMERA_INDEX=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_AUTOFOCUS_ENABLED=true
CAMERA_AUTOFOCUS_MODE=continuous
CAMERA_AUTOFOCUS_SPEED=fast
CAMERA_AUTOFOCUS_WARMUP_SECONDS=1.2
```

Run one of these commands:

```bash
python main.py
```

or

```bash
python capture_server.py
```

## Required Next.js API endpoints

```txt
GET /api/devices/by-code/:deviceCode
GET /api/attendance-sessions/active?deviceCode=
POST /api/checkins/face
POST /api/devices/:deviceId/heartbeat
```

## Required shared configuration

The Raspberry Pi `DEVICE_TOKEN` must match `FRAS_DEVICE_TOKEN` in the Next.js app.

The Next.js app must also be configured to reach the AI service using:

```txt
FRAS_AI_BASE_URL
FRAS_AI_SHARED_KEY
```

## Manual face capture

If you want to manually collect cropped face images on the Pi without sending anything to the server, run:

```bash
python manual_capture.py
```

This uses the same camera, face detection, and face crop logic as the attendance flow, then saves cropped face images into a timestamped folder under:

```txt
captures/manual_faces/
```

Useful options:

```bash
python manual_capture.py --cooldown 2 --max-images 6
python manual_capture.py --output-dir captures/student_a
python manual_capture.py --no-quality-check
```

Notes:
- The preview window stays open while capturing.
- Press `q` or `Esc` to stop.
- Images are throttled by the cooldown so they are not saved too fast.
