"""Synthetic detections for demo mode when no camera/AI process is attached."""

import math
import random
import time


def generate_demo_detections(frame_id: int) -> list[dict]:
    t = time.time()
    detections = []

    # Lead vehicle approaching
    lead_y = 200 + 80 * math.sin(t * 0.4)
    detections.append(
        {
            "x1": 280,
            "y1": lead_y,
            "x2": 360,
            "y2": lead_y + 70,
            "confidence": 0.88,
            "class_name": "car",
            "track_id": 1,
        }
    )

    # Side vehicle (blind spot scenario)
    if frame_id % 40 < 25:
        detections.append(
            {
                "x1": 80,
                "y1": 300,
                "x2": 140,
                "y2": 360,
                "confidence": 0.75,
                "class_name": "car",
                "track_id": 2,
            }
        )

    # Pedestrian
    if int(t) % 15 < 8:
        px = 400 + 30 * math.sin(t * 0.8)
        detections.append(
            {
                "x1": px,
                "y1": 350,
                "x2": px + 40,
                "y2": 420,
                "confidence": 0.82,
                "class_name": "person",
                "track_id": 3,
            }
        )

    return detections


def generate_demo_lanes() -> list[list[tuple[float, float]]]:
    left, right = [], []
    for y in range(0, 480, 20):
        left.append((180 + 20 * math.sin(y / 80), y))
        right.append((460 - 15 * math.sin(y / 90), y))
    return [left, right]
