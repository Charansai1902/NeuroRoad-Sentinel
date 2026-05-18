"""Cooperative V2V communication simulation."""

import math
import random
import time

from backend.api.schemas import V2VMessage


class V2VSimulator:
    def __init__(self, num_vehicles: int = 4):
        self._vehicles = [f"VEH-{i:03d}" for i in range(num_vehicles)]

    def broadcast(self, ego_speed: float, ego_risk: float) -> list[V2VMessage]:
        messages = []
        t = time.time()
        for i, vid in enumerate(self._vehicles):
            angle = (t * 0.5 + i * 1.2) % 6.28
            x = 30 * random.uniform(0.8, 1.2) * (1 if i % 2 else -1) * (i + 1) / 3
            y = 40 + 20 * math.sin(angle)

            risk = random.uniform(0.1, 0.7)
            sudden = risk > 0.6 and random.random() > 0.85
            messages.append(
                V2VMessage(
                    vehicle_id=vid,
                    position=(x, y),
                    speed_kmh=ego_speed * random.uniform(0.7, 1.1),
                    risk_level=risk,
                    sudden_brake=sudden,
                )
            )
        return messages
