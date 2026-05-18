"""Driver behavior analysis from temporal speed/steering patterns."""

from dataclasses import dataclass


@dataclass
class BehaviorSnapshot:
    harsh_brake: bool
    rapid_lane_change: bool
    speeding: bool
    score_delta: float


class DriverBehaviorAnalyzer:
    def __init__(self, speed_limit_kmh: float = 100.0):
        self.speed_limit = speed_limit_kmh
        self._prev_speed: float | None = None

    def analyze(self, speed_kmh: float, lane_offset: float, front_dist: float) -> BehaviorSnapshot:
        harsh = False
        if self._prev_speed is not None and self._prev_speed - speed_kmh > 15:
            harsh = True
        self._prev_speed = speed_kmh

        rapid_lane = abs(lane_offset) > 0.4
        speeding = speed_kmh > self.speed_limit
        delta = -5.0 if harsh else 0.0
        delta += -3.0 if rapid_lane else 0.0
        delta += -4.0 if speeding else 0.0
        if front_dist < 10:
            delta -= 8.0

        return BehaviorSnapshot(
            harsh_brake=harsh,
            rapid_lane_change=rapid_lane,
            speeding=speeding,
            score_delta=delta,
        )
