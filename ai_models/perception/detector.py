"""YOLOv8 real-time vehicle & pedestrian detection."""

from __future__ import annotations

import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None  # type: ignore

TARGET_CLASSES = frozenset(
    {"person", "car", "truck", "bus", "motorcycle", "bicycle"}
)


class ObjectDetector:
    def __init__(self, model_name: str = "yolov8n.pt", conf: float = 0.45):
        self.conf = conf
        self.model_name = model_name
        self.model = None
        if YOLO is not None:
            try:
                self.model = YOLO(model_name)
            except Exception:
                self.model = None

    @property
    def available(self) -> bool:
        return self.model is not None

    def detect(self, frame: np.ndarray) -> list[dict]:
        if self.model is None:
            return []

        results = self.model(frame, conf=self.conf, verbose=False)[0]
        detections = []
        names = results.names
        for box in results.boxes:
            cls_id = int(box.cls[0])
            name = names[cls_id]
            if name not in TARGET_CLASSES:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(
                {
                    "x1": float(x1),
                    "y1": float(y1),
                    "x2": float(x2),
                    "y2": float(y2),
                    "confidence": float(box.conf[0]),
                    "class_name": name,
                    "track_id": None,
                }
            )
        return detections
