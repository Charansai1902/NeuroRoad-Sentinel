from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "NeuroRoad Sentinel"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    collision_horizon_sec: float = 5.0
    risk_threshold: float = 0.65

    # Live perception
    perception_enabled: bool = True
    demo_mode: bool = False
    # 0 = webcam, or absolute path to .mp4 for live demo recording
    camera_source: int | str = 0
    video_loop: bool = True
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 30
    target_fps: int = 12
    yolo_model: str = "yolov8n.pt"
    yolo_conf: float = 0.45
    focal_scale: float = 0.92
    track_max_age: int = 30
    jpeg_quality: int = 72
    default_ego_speed_kmh: float = 30.0

    class Config:
        env_file = ".env"


settings = Settings()
