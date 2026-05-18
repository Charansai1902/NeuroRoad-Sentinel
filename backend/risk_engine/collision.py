"""Future collision forecasting — 3–5 second horizon risk estimation."""

import math
from dataclasses import dataclass

from backend.api.schemas import Alert, AlertAction, AlertLevel, RiskZone, TrajectoryPoint
from backend.risk_engine.explainable import build_explanation
from backend.risk_engine.intention import IntentionPredictor


@dataclass
class CollisionAssessment:
    collision_probability: float
    time_to_collision_sec: float | None
    risk_heatmap: list[RiskZone]
    trajectories: dict[str, list[TrajectoryPoint]]
    alerts: list[Alert]


class CollisionForecaster:
    HORIZON_SEC = 5.0
    STEPS = 10

    def __init__(self):
        self._intention = IntentionPredictor()

    def _predict_path(
        self, x: float, y: float, vx: float, vy: float, prefix: str
    ) -> list[TrajectoryPoint]:
        points = []
        dt = self.HORIZON_SEC / self.STEPS
        for i in range(self.STEPS + 1):
            t = i * dt
            points.append(
                TrajectoryPoint(
                    t=t,
                    x=x + vx * t,
                    y=y + vy * t,
                    confidence=max(0.3, 1.0 - i * 0.07),
                )
            )
        return points

    def _paths_overlap(
        self, ego_path: list[TrajectoryPoint], obj_path: list[TrajectoryPoint], threshold: float = 8.0
    ) -> tuple[bool, float]:
        min_dist = float("inf")
        for ep, op in zip(ego_path, obj_path):
            d = math.hypot(ep.x - op.x, ep.y - op.y)
            min_dist = min(min_dist, d)
        return min_dist < threshold, min_dist

    def assess(
        self,
        ego_speed_kmh: float,
        radar_front_m: float,
        object_states: list[dict],
        heading_rate: float = 0.0,
    ) -> CollisionAssessment:
        ego_vy = ego_speed_kmh / 3.6
        ego_path = self._predict_path(0.0, 0.0, 0.0, ego_vy, "ego")
        trajectories: dict[str, list[TrajectoryPoint]] = {"ego": ego_path}

        max_prob = 0.0
        min_ttc: float | None = None
        factors: list[str] = []
        heatmap: list[RiskZone] = []

        for obj in object_states:
            tid = obj["track_id"]
            pos = obj["position"]
            vel = obj["velocity"]
            key = f"obj_{tid}"
            obj_path = self._predict_path(pos[0], pos[1], vel[0], vel[1], key)
            trajectories[key] = obj_path

            overlap, dist = self._paths_overlap(ego_path, obj_path)
            rel_speed = max(0.1, ego_vy - vel[1])
            ttc = pos[1] / rel_speed if pos[1] > 0 and rel_speed > 0 else None

            if overlap:
                prob = min(0.95, 0.5 + (8.0 - dist) / 16.0)
                factors.append(f"Trajectory overlap with {obj['class_name']} (track {tid})")
            else:
                prob = max(0.0, 0.4 - dist / 50.0) if pos[1] < 60 else 0.05

            if radar_front_m < 20:
                prob = min(0.98, prob + (20 - radar_front_m) / 40)
                factors.append(f"Front radar distance {radar_front_m:.1f}m")

            max_prob = max(max_prob, prob)
            if ttc is not None and (min_ttc is None or ttc < min_ttc):
                min_ttc = ttc

            heatmap.append(
                RiskZone(x=pos[0], y=pos[1], intensity=prob, label=obj["class_name"])
            )

        # Grid heatmap ahead of ego
        for i in range(-3, 4):
            for j in range(1, 8):
                x, y = i * 12.0, j * 15.0
                base = max(0.0, 0.6 - y / 100.0)
                if radar_front_m < y:
                    base += 0.2
                heatmap.append(RiskZone(x=x, y=y, intensity=min(1.0, base), label="road"))

        intention = self._intention.predict(ego_speed_kmh, heading_rate, radar_front_m)
        if intention.lane_change_probability > 0.5:
            factors.append("Rapid lane deviation pattern detected")
        if intention.sudden_brake_probability > 0.5:
            factors.append("Sudden braking probability elevated")

        alerts: list[Alert] = []
        explanation = build_explanation(max_prob, factors, min_ttc)

        if max_prob >= 0.75:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    action=AlertAction.BRAKE,
                    message="Emergency braking recommended",
                    explanation=explanation,
                    collision_probability=max_prob,
                    time_to_collision_sec=min_ttc,
                )
            )
        elif max_prob >= 0.5:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    action=AlertAction.SLOW_DOWN,
                    message="Reduce speed — collision risk ahead",
                    explanation=explanation,
                    collision_probability=max_prob,
                    time_to_collision_sec=min_ttc,
                )
            )
        elif max_prob >= 0.35:
            alerts.append(
                Alert(
                    level=AlertLevel.INFO,
                    action=AlertAction.DRIVER_WARNING,
                    message="Monitor adjacent traffic",
                    explanation=explanation,
                    collision_probability=max_prob,
                    time_to_collision_sec=min_ttc,
                )
            )

        if radar_front_m < 8:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    action=AlertAction.COLLISION_AVOID,
                    message="Imminent front collision risk",
                    explanation=build_explanation(
                        0.9, ["Very close front object"], min_ttc
                    ),
                    collision_probability=0.9,
                    time_to_collision_sec=min_ttc,
                )
            )

        return CollisionAssessment(
            collision_probability=max_prob,
            time_to_collision_sec=min_ttc,
            risk_heatmap=heatmap,
            trajectories=trajectories,
            alerts=alerts,
        )
