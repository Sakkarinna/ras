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
