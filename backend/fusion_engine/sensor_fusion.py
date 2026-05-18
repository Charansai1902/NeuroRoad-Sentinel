"""Multi-sensor fusion: vision-derived range + Kalman object states."""

import math
import time
from dataclasses import dataclass, field

from backend.config import settings
from backend.fusion_engine.kalman import VehicleStateKalman


@dataclass
class FusedState:
    timestamp: float
    ego_speed_kmh: float
    ego_heading_deg: float
    gps_lat: float
    gps_lon: float
    imu_yaw: float
    imu_pitch: float
    radar_front_m: float
    radar_rear_m: float
    radar_left_m: float
    radar_right_m: float
    fused_position: tuple[float, float]
    fused_velocity: tuple[float, float]
    object_states: list[dict] = field(default_factory=list)


class SensorFusionEngine:
    def __init__(self):
        self._ego_kalman = VehicleStateKalman(dt=0.1)
        self._track_kalmans: dict[int, VehicleStateKalman] = {}
        self._t0 = time.time()
        self._base_lat, self._base_lon = 37.7749, -122.4194

    def _vision_ranges(
        self, detections: list[dict], frame_shape: tuple[int, int] | None
    ) -> tuple[float, float, float, float]:
        """Derive pseudo-radar from monocular distances and image position."""
        if not detections or not frame_shape:
            return 100.0, 80.0, 50.0, 50.0

        h, w = frame_shape
        front, left, right, rear = 100.0, 50.0, 50.0, 80.0

        for det in detections:
            dist = det.get("distance_m")
            if dist is None:
                continue
            cx = (det["x1"] + det["x2"]) / 2.0
            cy = (det["y1"] + det["y2"]) / 2.0

            if cy > h * 0.35 and abs(cx - w / 2) < w * 0.38:
                front = min(front, dist)
            elif cx < w * 0.28 and cy > h * 0.4:
                left = min(left, dist)
            elif cx > w * 0.72 and cy > h * 0.4:
                right = min(right, dist)
            elif cy < h * 0.35:
                rear = min(rear, dist)

        return front, rear, left, right

    def fuse(
        self,
        detections: list[dict],
        speed_kmh: float | None = None,
        frame_id: int = 0,
        frame_shape: tuple[int, int] | None = None,
        live_mode: bool = False,
    ) -> FusedState:
        t = time.time()
        elapsed = t - self._t0

        if live_mode:
            speed = speed_kmh if speed_kmh is not None else settings.default_ego_speed_kmh
            heading = 0.0
            lat = self._base_lat
            lon = self._base_lon
            front, rear, left, right = self._vision_ranges(detections, frame_shape)
        else:
            speed = speed_kmh if speed_kmh is not None else 45.0 + 5.0 * math.sin(elapsed * 0.3)
            heading = (elapsed * 12.0) % 360.0
            lat = self._base_lat + 0.0001 * math.sin(elapsed * 0.1)
            lon = self._base_lon + 0.0001 * math.cos(elapsed * 0.1)
            front, rear, left, right = 100.0, 80.0, 50.0, 50.0

        self._ego_kalman.predict()
        ego_state = self._ego_kalman.update((0.0, 0.0))

        fw = frame_shape[1] if frame_shape else 640
        fh = frame_shape[0] if frame_shape else 480
        object_states = []

        for det in detections:
            tid = det.get("track_id")
            if tid is None:
                continue

            cx = (det["x1"] + det["x2"]) / 2.0
            cy = (det["y1"] + det["y2"]) / 2.0
            dist = det.get("distance_m")

            if live_mode and dist is not None:
                world_x = (cx / fw - 0.5) * dist * 1.2
                world_y = dist
                vx = det.get("closing_speed_ms", 0.0) * 0.1
                vy = det.get("closing_speed_ms", 0.0)
            else:
                world_x = cx / fw * 80.0 - 40.0
                world_y = 100.0 - cy / fh * 120.0
                vx, vy = 0.0, 0.0

            if tid not in self._track_kalmans:
                self._track_kalmans[tid] = VehicleStateKalman(dt=0.1)
            kf = self._track_kalmans[tid]
            kf.predict()
            state = kf.update((world_x, world_y))

            object_states.append(
                {
                    "track_id": tid,
                    "class_name": det.get("class_name", "vehicle"),
                    "position": (float(state[0]), float(state[1])),
                    "velocity": (float(state[2] + vx), float(state[3] + vy)),
                    "confidence": det.get("confidence", 0.5),
                    "distance_m": dist,
                    "ttc_sec": det.get("ttc_sec"),
                }
            )

        if not live_mode:
            front_objs = [o for o in object_states if o["position"][1] > 10]
            front = min((o["position"][1] for o in front_objs), default=100.0)

        return FusedState(
            timestamp=t,
            ego_speed_kmh=speed,
            ego_heading_deg=heading,
            gps_lat=lat,
            gps_lon=lon,
            imu_yaw=math.radians(heading),
            imu_pitch=0.02 * math.sin(elapsed) if not live_mode else 0.0,
            radar_front_m=max(1.5, front),
            radar_rear_m=max(2.0, rear),
            radar_left_m=max(1.5, left),
            radar_right_m=max(1.5, right),
            fused_position=(float(ego_state[0]), float(ego_state[1])),
            fused_velocity=(float(ego_state[2]), float(ego_state[3])),
            object_states=object_states,
        )
