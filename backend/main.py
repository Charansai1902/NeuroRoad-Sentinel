"""NeuroRoad Sentinel — FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings
from backend.perception.engine import perception_engine
from backend.websocket.stream import websocket_endpoint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.perception_enabled:
        perception_engine.start()
        logger.info("Live perception engine started")
    yield
    if settings.perception_enabled:
        perception_engine.stop()
        logger.info("Live perception engine stopped")


app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Cooperative ADAS & Autonomous Risk Prediction",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket_endpoint(websocket)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "live_mode": settings.perception_enabled and not settings.demo_mode,
        "perception": perception_engine.status,
        "docs": "/docs",
        "websocket": "/ws/stream",
    }
