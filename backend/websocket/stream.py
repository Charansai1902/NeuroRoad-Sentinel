import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from backend.config import settings
from backend.perception.frame_hub import frame_hub
from backend.services.demo_generator import generate_demo_detections, generate_demo_lanes
from backend.services.pipeline import pipeline


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    frame_id = 0
    try:
        while True:
            payload = frame_hub.get_latest()

            if payload is None and settings.demo_mode:
                dets = generate_demo_detections(frame_id)
                lanes = generate_demo_lanes()
                frame = pipeline.process_frame(dets, lanes, live_mode=False)
                payload = json.loads(frame.model_dump_json())
                payload["live_mode"] = False

            if payload is None:
                await asyncio.sleep(0.05)
                continue

            await websocket.send_json(payload)
            frame_id += 1
            interval = 1.0 / max(settings.target_fps, 1)
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
