"""Real-time collision risk from vision distance, velocity, and TTC."""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.api.schemas import Alert, AlertAction, AlertLevel, RiskZone, TrajectoryPoint
from backend.risk_engine.explainable import build_explanation


@dataclass
class VisionCollisionAssessment:
    collision_probability: float
    time_to_collision_sec: float | None
    risk_heatmap: list[RiskZone]
    trajectories: dict[str, list[TrajectoryPoint]]
    alerts: list[Alert]
    front_distance_m: float


class VisionCollisionEngine:
    HORIZON = 5.0
    STEPS = 10

    def assess(self, detections: list[dict], frame_shape: tuple[int, int]) -> VisionCollisionAssessment:
        h, w = frame_shape
        max_prob = 0.0
        min_ttc: float | None = None
        min_front = 100.0
        factors: list[str] = []
        heatmap: list[RiskZone] = []
        trajectories: dict[str, list[TrajectoryPoint]] = {"ego": self._ego_path()}

        for det in detections:
            tid = det.get("track_id")
            if tid is None:
                continue

            dist = det.get("distance_m", 100.0)
            ttc = det.get("ttc_sec")
            prob = det.get("collision_probability", 0.0)
            cx = (det["x1"] + det["x2"]) / 2.0
            cy = (det["y1"] + det["y2"]) / 2.0

            # Front zone: lower image, near center
            if cy > h * 0.3 and abs(cx - w / 2) < w * 0.4:
                min_front = min(min_front, dist)

            if det.get("in_ego_path"):
                max_prob = max(max_prob, prob)
                if ttc is not None and (min_ttc is None or ttc < min_ttc):
                    min_ttc = ttc
                factors.append(
                    f"{det['class_name']} track {tid}: {dist:.1f}m"
                    + (f", TTC {ttc:.1f}s" if ttc else "")
                )

            # World coords for twin (normalized)
            wx = (cx / w - 0.5) * 80.0
            wy = (1.0 - cy / h) * 100.0
            vel = det.get("closing_speed_ms", 0.0)
            trajectories[f"obj_{tid}"] = self._object_path(wx, wy, 0.0, vel)

            heatmap.append(
                RiskZone(
                    x=wx,
                    y=wy,
                    intensity=min(1.0, prob),
                    label=det.get("class_name", "object"),
                )
            )

        alerts = self._build_alerts(max_prob, min_ttc, min_front, factors)

        return VisionCollisionAssessment(
            collision_probability=max_prob,
            time_to_collision_sec=min_ttc,
            risk_heatmap=heatmap,
            trajectories=trajectories,
            alerts=alerts,
            front_distance_m=min_front,
        )

    def _ego_path(self) -> list[TrajectoryPoint]:
        pts = []
        dt = self.HORIZON / self.STEPS
        for i in range(self.STEPS + 1):
            t = i * dt
            pts.append(TrajectoryPoint(t=t, x=0.0, y=t * 12.0, confidence=1.0 - i * 0.05))
        return pts

    def _object_path(self, x: float, y: float, vx: float, vy: float) -> list[TrajectoryPoint]:
        pts = []
        dt = self.HORIZON / self.STEPS
        for i in range(self.STEPS + 1):
            t = i * dt
            pts.append(
                TrajectoryPoint(
                    t=t,
                    x=x + vx * t,
                    y=y + vy * t * 10,
                    confidence=max(0.3, 1.0 - i * 0.08),
                )
            )
        return pts

    def _build_alerts(
        self,
        max_prob: float,
        min_ttc: float | None,
        front_m: float,
        factors: list[str],
    ) -> list[Alert]:
        alerts: list[Alert] = []
        explanation = build_explanation(max_prob, factors or ["No threats in ego path"], min_ttc)

        if max_prob >= 0.75 or (min_ttc is not None and min_ttc < 1.5):
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    action=AlertAction.BRAKE,
                    message="Emergency braking — imminent collision risk",
                    explanation=explanation,
                    collision_probability=max_prob,
                    time_to_collision_sec=min_ttc,
                )
            )
        elif max_prob >= 0.5 or (min_ttc is not None and min_ttc < 3.0):
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    action=AlertAction.SLOW_DOWN,
                    message="Reduce speed — object closing rapidly",
                    explanation=explanation,
                    collision_probability=max_prob,
                    time_to_collision_sec=min_ttc,
                )
            )
        elif max_prob >= 0.3:
            alerts.append(
                Alert(
                    level=AlertLevel.INFO,
                    action=AlertAction.DRIVER_WARNING,
                    message="Monitor forward path",
                    explanation=explanation,
                    collision_probability=max_prob,
                    time_to_collision_sec=min_ttc,
                )
            )

        if front_m < 5.0:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    action=AlertAction.COLLISION_AVOID,
                    message=f"Critical proximity: {front_m:.1f}m",
                    explanation=build_explanation(0.92, [f"Front object at {front_m:.1f}m"], min_ttc),
                    collision_probability=0.92,
                    time_to_collision_sec=min_ttc,
                )
            )

        return alerts
