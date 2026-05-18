"""Monocular distance, velocity, TTC, and collision probability from tracked boxes."""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field

# Real-world reference heights (meters) for pinhole distance estimation
CLASS_HEIGHT_M: dict[str, float] = {
    "person": 1.7,
    "car": 1.5,
    "truck": 2.5,
    "bus": 3.0,
    "motorcycle": 1.2,
    "bicycle": 1.0,
}

TARGET_CLASSES = {"person", "car", "truck", "bus", "motorcycle", "bicycle"}


@dataclass
class TrackHistory:
    samples: deque = field(default_factory=lambda: deque(maxlen=30))


class MonocularMetrics:
    """Enriches detections with distance_m, velocity_ms, ttc_sec, collision_probability."""

    def __init__(self, focal_scale: float = 0.92):
        self.focal_scale = focal_scale
        self._history: dict[int, TrackHistory] = {}

    def _focal_pixels(self, frame_width: int) -> float:
        return frame_width * self.focal_scale

    def estimate_distance(self, bbox_height: float, class_name: str, focal_px: float) -> float:
        h_real = CLASS_HEIGHT_M.get(class_name, 1.5)
        return float((h_real * focal_px) / max(bbox_height, 8.0))

    def _collision_probability(self, distance_m: float, ttc_sec: float | None) -> float:
        if ttc_sec is not None and ttc_sec > 0:
            if ttc_sec < 1.0:
                return 0.95
            if ttc_sec < 2.0:
                return 0.82
            if ttc_sec < 3.5:
                return 0.62
            if ttc_sec < 5.0:
                return 0.38
            return max(0.05, 0.25 - ttc_sec * 0.03)
        if distance_m < 4:
            return 0.9
        if distance_m < 8:
            return 0.7
        if distance_m < 15:
            return 0.45
        if distance_m < 25:
            return 0.2
        return 0.05

    def enrich(
        self,
        detections: list[dict],
        frame_shape: tuple[int, int],
    ) -> list[dict]:
        h, w = frame_shape
        focal = self._focal_pixels(w)
        now = time.time()
        cx_img = w / 2.0

        for det in detections:
            tid = det.get("track_id")
            if tid is None:
                continue

            x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
            bbox_h = y2 - y1
            bbox_w = x2 - x1
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            class_name = det.get("class_name", "car")
            distance = self.estimate_distance(bbox_h, class_name, focal)

            # Objects higher in frame are farther; scale by vertical position
            vertical_factor = 0.85 + 0.3 * (cy / max(h, 1))
            distance *= vertical_factor

            if tid not in self._history:
                self._history[tid] = TrackHistory()
            hist = self._history[tid].samples
            hist.append((now, distance, cx, cy, bbox_h))

            velocity_ms = 0.0
            ttc_sec: float | None = None
            closing_speed = 0.0

            if len(hist) >= 2:
                t0, d0, cx0, _, _ = hist[-2]
                t1, d1, cx1, _, _ = hist[-1]
                dt = max(t1 - t0, 1e-3)
                velocity_ms = (d0 - d1) / dt  # positive = approaching
                lateral_v = (cx1 - cx0) / dt
                velocity_ms = math.hypot(velocity_ms, lateral_v * 0.02)

                closing_speed = (d0 - d1) / dt
                if closing_speed > 0.3 and d1 > 0.5:
                    ttc_sec = d1 / closing_speed

            # Front-threat: center lane + lower half of image
            in_path = abs(cx - cx_img) < w * 0.35 and cy > h * 0.35
            col_prob = self._collision_probability(distance, ttc_sec if in_path else None)
            if not in_path:
                col_prob *= 0.45

            det["distance_m"] = round(distance, 2)
            det["velocity_ms"] = round(velocity_ms, 2)
            det["closing_speed_ms"] = round(closing_speed, 2)
            det["ttc_sec"] = round(ttc_sec, 2) if ttc_sec is not None else None
            det["collision_probability"] = round(col_prob, 3)
            det["in_ego_path"] = in_path
            det["bbox_w"] = bbox_w
            det["bbox_h"] = bbox_h

        # Prune stale tracks
        active = {d.get("track_id") for d in detections if d.get("track_id")}
        for tid in list(self._history):
            if tid not in active:
                del self._history[tid]

        return detections
