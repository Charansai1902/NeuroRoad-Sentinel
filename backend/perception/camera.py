"""OpenCV webcam / video file capture with optional loop for demos."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


class CameraStream:
    def __init__(
        self,
        source: int | str = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        loop_video: bool = True,
    ):
        self.source = source
        self.width = width
        self.height = height
        self.target_fps = fps
        self.loop_video = loop_video
        self._cap: cv2.VideoCapture | None = None
        self._is_video_file = False
        self._label = "webcam"

    @property
    def input_label(self) -> str:
        return self._label

    @property
    def is_video_file(self) -> bool:
        return self._is_video_file

    def _resolve_source(self):
        if isinstance(self.source, int) or (
            isinstance(self.source, str) and str(self.source).isdigit()
        ):
            return int(self.source), False
        path = Path(str(self.source))
        if path.suffix.lower() in VIDEO_EXTENSIONS:
            return str(path.resolve()), True
        return self.source, False

    def open(self) -> bool:
        src, is_file = self._resolve_source()
        self._is_video_file = is_file
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            logger.error("Input failed to open: %s", self.source)
            return False

        if is_file:
            self._label = Path(str(self.source)).name
            # Use native video resolution for best detection quality
            vw = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            vh = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if vw > 0 and vh > 0:
                self.width, self.height = vw, vh
            logger.info("Video file opened: %s (%dx%d, loop=%s)", self._label, self.width, self.height, self.loop_video)
        else:
            self._label = "webcam"
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            logger.info("Webcam opened (%dx%d)", self.width, self.height)
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self._cap is None or not self._cap.isOpened():
            return False, None

        ok, frame = self._cap.read()
        if not ok and self._is_video_file and self.loop_video:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
            if ok:
                logger.debug("Video looped to start: %s", self._label)

        return ok, frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()
