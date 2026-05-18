"""JPEG encoding for WebSocket camera stream."""

import base64

import cv2
import numpy as np


def frame_to_base64_jpeg(frame: np.ndarray, quality: int = 72) -> str:
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("ascii")
