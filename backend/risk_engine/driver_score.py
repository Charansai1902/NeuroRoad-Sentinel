"""Driver behavior scoring module."""

import time

from backend.api.schemas import DriverScore


class DriverScoreEngine:
    def __init__(self):
        self._history: list[dict] = []
        self._session_start = time.time()

    def update(
        self,
        ego_speed_kmh: float,
        aggression: float,
        brake_events: int,
        lane_deviation: float,
    ) -> DriverScore:
        self._history.append(
            {
                "speed": ego_speed_kmh,
                "aggression": aggression,
                "brake": brake_events,
                "lane": lane_deviation,
            }
        )
        if len(self._history) > 200:
            self._history = self._history[-200:]

        avg_speed = sum(h["speed"] for h in self._history) / len(self._history)
        avg_agg = sum(h["aggression"] for h in self._history) / len(self._history)
        avg_lane = sum(h["lane"] for h in self._history) / len(self._history)

        speed_compliance = max(0, 100 - max(0, avg_speed - 100) * 1.5)
        safe = max(0, 100 - avg_agg * 60 - avg_lane * 30)
        sudden_braking = max(0, 100 - brake_events * 8)
        lane_discipline = max(0, 100 - avg_lane * 80)
        aggression_score = max(0, 100 - avg_agg * 70)

        overall = (
            safe * 0.35
            + speed_compliance * 0.2
            + sudden_braking * 0.15
            + lane_discipline * 0.2
            + aggression_score * 0.1
        )

        return DriverScore(
            overall=round(overall, 1),
            safe_driving=round(safe, 1),
            aggression=round(aggression_score, 1),
            sudden_braking=round(sudden_braking, 1),
            lane_discipline=round(lane_discipline, 1),
            speed_compliance=round(speed_compliance, 1),
        )
