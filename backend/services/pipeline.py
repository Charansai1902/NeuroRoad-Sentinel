"""Central perception → fusion → intelligence → decision pipeline."""

import time

from backend.api.schemas import BoundingBox, PerceptionFrame, SensorReading
from backend.config import settings
from backend.decision_engine.planner import DecisionEngine
from backend.fusion_engine.sensor_fusion import SensorFusionEngine
from backend.risk_engine.collision import CollisionForecaster
from backend.risk_engine.driver_score import DriverScoreEngine
from backend.risk_engine.intention import IntentionPredictor
from backend.risk_engine.vision_collision import VisionCollisionEngine
from backend.services.v2v_sim import V2VSimulator


class SentinelPipeline:
    def __init__(self):
        self.fusion = SensorFusionEngine()
        self.collision = CollisionForecaster()
        self.vision_collision = VisionCollisionEngine()
        self.intention = IntentionPredictor()
        self.driver_score = DriverScoreEngine()
        self.decision = DecisionEngine()
        self.v2v = V2VSimulator()
        self._frame_id = 0
        self._brake_events = 0

    def process_frame(
        self,
        detections: list[dict] | None = None,
        lanes: list[list[tuple[float, float]]] | None = None,
        frame_shape: tuple[int, int] | None = None,
        live_mode: bool = False,
        speed_kmh: float | None = None,
    ) -> PerceptionFrame:
        self._frame_id += 1
        detections = detections or []

        fused = self.fusion.fuse(
            detections,
            speed_kmh=speed_kmh,
            frame_id=self._frame_id,
            frame_shape=frame_shape,
            live_mode=live_mode,
        )

        if live_mode and frame_shape:
            assessment = self.vision_collision.assess(detections, frame_shape)
            fused.radar_front_m = assessment.front_distance_m
        else:
            sim = self.collision.assess(
                fused.ego_speed_kmh,
                fused.radar_front_m,
                fused.object_states,
            )
            assessment = sim

        intention = self.intention.predict(
            fused.ego_speed_kmh,
            heading_rate=0.0,
            front_distance_m=fused.radar_front_m,
        )
        if intention.sudden_brake_probability > 0.6:
            self._brake_events += 1

        score = self.driver_score.update(
            fused.ego_speed_kmh,
            intention.aggressive_driving_score,
            self._brake_events,
            intention.lane_change_probability,
        )

        alerts = list(assessment.alerts)
        bs = self.decision.blind_spot_alert(fused.radar_left_m, fused.radar_right_m)
        if bs:
            alerts.append(bs)
        alerts = self.decision.prioritize(alerts)

        boxes = [
            BoundingBox(
                x1=d["x1"],
                y1=d["y1"],
                x2=d["x2"],
                y2=d["y2"],
                confidence=d.get("confidence", 0.5),
                class_name=d.get("class_name", "vehicle"),
                track_id=d.get("track_id"),
                distance_m=d.get("distance_m"),
                velocity_ms=d.get("velocity_ms"),
                ttc_sec=d.get("ttc_sec"),
                collision_probability=d.get("collision_probability"),
                in_ego_path=d.get("in_ego_path"),
            )
            for d in detections
        ]

        v2v = (
            self._v2v_from_tracks(detections)
            if live_mode
            else self.v2v.broadcast(fused.ego_speed_kmh, assessment.collision_probability)
        )

        return PerceptionFrame(
            timestamp=time.time(),
            frame_id=self._frame_id,
            detections=boxes,
            lanes=lanes or [],
            trajectories=assessment.trajectories,
            risk_heatmap=assessment.risk_heatmap,
            sensors=SensorReading(
                gps_lat=fused.gps_lat,
                gps_lon=fused.gps_lon,
                speed_kmh=fused.ego_speed_kmh,
                heading_deg=fused.ego_heading_deg,
                imu_yaw=fused.imu_yaw,
                imu_pitch=fused.imu_pitch,
                radar_front_m=fused.radar_front_m,
                radar_rear_m=fused.radar_rear_m,
                radar_left_m=fused.radar_left_m,
                radar_right_m=fused.radar_right_m,
            ),
            alerts=alerts,
            driver_score=score,
            v2v_messages=v2v,
            live_mode=live_mode,
            metadata={
                "collision_probability": assessment.collision_probability,
                "time_to_collision_sec": assessment.time_to_collision_sec,
                "driver_intent": intention.primary_intent,
                "lane_change_prob": intention.lane_change_probability,
                "top_alert": alerts[0].action.value if alerts else "none",
                "front_distance_m": fused.radar_front_m,
                "track_count": len([d for d in detections if d.get("track_id")]),
            },
        )

    def _v2v_from_tracks(self, detections: list[dict]):
        from backend.api.schemas import V2VMessage

        messages = []
        for d in detections:
            tid = d.get("track_id")
            if tid is None:
                continue
            dist = d.get("distance_m", 50.0)
            risk = d.get("collision_probability", 0.1)
            cx = (d["x1"] + d["x2"]) / 2.0
            cy = (d["y1"] + d["y2"]) / 2.0
            messages.append(
                V2VMessage(
                    vehicle_id=f"TRACK-{tid}",
                    position=(cx / 10.0 - 32.0, dist),
                    speed_kmh=settings.default_ego_speed_kmh * 0.9,
                    risk_level=risk,
                    sudden_brake=risk > 0.75 and (d.get("ttc_sec") or 99) < 2.0,
                )
            )
        return messages[:6]


pipeline = SentinelPipeline()
