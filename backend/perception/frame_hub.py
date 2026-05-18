"""Thread-safe hub for latest perception frame + telemetry."""

from __future__ import annotations

import threading
import time
from typing import Any

from backend.api.schemas import PerceptionFrame


class FrameHub:
    def __init__(self):
        self._lock = threading.Lock()
        self._frame: PerceptionFrame | None = None
        self._payload: dict[str, Any] | None = None
        self._fps: float = 0.0
        self._running = False
        self._last_ts = 0.0

    def update(self, frame: PerceptionFrame, payload: dict[str, Any] | None = None) -> None:
        now = time.time()
        with self._lock:
            if self._last_ts > 0:
                dt = now - self._last_ts
                if dt > 0:
                    self._fps = 0.85 * self._fps + 0.15 * (1.0 / dt)
            self._last_ts = now
            self._frame = frame
            self._payload = payload

    def get_latest(self) -> dict[str, Any] | None:
        with self._lock:
            if self._frame is None:
                return None
            data = self._frame.model_dump()
            data["fps"] = round(self._fps, 1)
            data["live_mode"] = True
            if self._payload:
                data.update(self._payload)
            return data

    def set_running(self, running: bool) -> None:
        with self._lock:
            self._running = running

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def has_frame(self) -> bool:
        with self._lock:
            return self._frame is not None


frame_hub = FrameHub()
