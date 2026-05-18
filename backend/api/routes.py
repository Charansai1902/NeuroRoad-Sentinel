from fastapi import APIRouter

from backend.api.schemas import HealthResponse, PerceptionFrame
from backend.config import settings
from backend.perception.engine import perception_engine
from backend.perception.frame_hub import frame_hub
from backend.services.demo_generator import generate_demo_detections, generate_demo_lanes
from backend.services.pipeline import pipeline

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health():
    status = perception_engine.status
    return HealthResponse(
        status="ok" if status.get("running") or settings.demo_mode else "degraded",
        service="NeuroRoad Sentinel",
        version="2.0.0",
        modules={
            "perception": "live" if status.get("running") else "offline",
            "camera": "ok" if status.get("camera") else "unavailable",
            "yolo": "ready" if status.get("yolo") else "fallback",
            "tracker": status.get("tracker", "unknown"),
            "fusion": "vision" if not settings.demo_mode else "simulated",
            "websocket": "ready",
        },
    )


@router.get("/perception/status")
async def perception_status():
    return perception_engine.status


@router.get("/telemetry", response_model=PerceptionFrame)
async def telemetry():
    latest = frame_hub.get_latest()
    if latest:
        return PerceptionFrame.model_validate(latest)
    if settings.demo_mode:
        dets = generate_demo_detections(0)
        lanes = generate_demo_lanes()
        return pipeline.process_frame(dets, lanes, live_mode=False)
    return pipeline.process_frame([], [], live_mode=True)


@router.get("/risk", response_model=PerceptionFrame)
async def risk():
    return await telemetry()


@router.get("/driver-score")
async def driver_score():
    frame = await telemetry()
    return frame.driver_score
