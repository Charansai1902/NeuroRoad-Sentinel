from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertAction(str, Enum):
    BRAKE = "brake"
    SLOW_DOWN = "slow_down"
    LANE_CORRECT = "lane_correct"
    BLIND_SPOT = "blind_spot"
    COLLISION_AVOID = "collision_avoid"
    DRIVER_WARNING = "driver_warning"
    NONE = "none"


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_name: str
    track_id: int | None = None
    distance_m: float | None = None
    velocity_ms: float | None = None
    ttc_sec: float | None = None
    collision_probability: float | None = None
    in_ego_path: bool | None = None


class TrajectoryPoint(BaseModel):
    t: float
    x: float
    y: float
    confidence: float = 1.0


class RiskZone(BaseModel):
    x: float
    y: float
    intensity: float
    label: str = ""


class SensorReading(BaseModel):
    gps_lat: float = 0.0
    gps_lon: float = 0.0
    speed_kmh: float = 0.0
    heading_deg: float = 0.0
    imu_yaw: float = 0.0
    imu_pitch: float = 0.0
    radar_front_m: float = 100.0
    radar_rear_m: float = 100.0
    radar_left_m: float = 50.0
    radar_right_m: float = 50.0


class V2VMessage(BaseModel):
    vehicle_id: str
    position: tuple[float, float]
    speed_kmh: float
    risk_level: float
    sudden_brake: bool = False


class ExplainableReason(BaseModel):
    summary: str
    factors: list[str] = Field(default_factory=list)
    confidence: float


class Alert(BaseModel):
    level: AlertLevel
    action: AlertAction
    message: str
    explanation: ExplainableReason
    collision_probability: float = 0.0
    time_to_collision_sec: float | None = None


class DriverScore(BaseModel):
    overall: float = Field(ge=0, le=100)
    safe_driving: float
    aggression: float
    sudden_braking: float
    lane_discipline: float
    speed_compliance: float


class PerceptionFrame(BaseModel):
    timestamp: float
    frame_id: int
    detections: list[BoundingBox] = Field(default_factory=list)
    lanes: list[list[tuple[float, float]]] = Field(default_factory=list)
    trajectories: dict[str, list[TrajectoryPoint]] = Field(default_factory=dict)
    risk_heatmap: list[RiskZone] = Field(default_factory=list)
    sensors: SensorReading
    alerts: list[Alert] = Field(default_factory=list)
    driver_score: DriverScore
    v2v_messages: list[V2VMessage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    camera_frame_jpeg: str | None = None
    live_mode: bool = False
    fps: float = 0.0


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str = "1.0.0"
    modules: dict[str, str]
