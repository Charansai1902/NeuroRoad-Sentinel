"""Driver intention prediction from motion trajectories."""

import math
from dataclasses import dataclass


@dataclass
class DriverIntention:
    lane_change_probability: float
    sudden_brake_probability: float
    aggressive_driving_score: float
    unsafe_overtake: bool
    primary_intent: str


class IntentionPredictor:
    def predict(
        self,
        ego_speed_kmh: float,
        heading_rate: float,
        front_distance_m: float,
        lateral_offset: float = 0.0,
    ) -> DriverIntention:
        lane_change = min(0.95, abs(lateral_offset) * 2.0 + abs(heading_rate) * 0.15)
        brake_prob = 0.0
        if front_distance_m < 25:
            brake_prob = min(0.9, (25 - front_distance_m) / 25)
        if front_distance_m < 12:
            brake_prob = min(0.98, brake_prob + 0.3)

        aggression = min(1.0, (ego_speed_kmh / 120.0) * 0.4 + abs(heading_rate) * 0.02)
        overtake = ego_speed_kmh > 90 and front_distance_m < 30 and lateral_offset > 0.3

        if brake_prob > 0.6:
            intent = "braking"
        elif lane_change > 0.5:
            intent = "lane_change"
        elif overtake:
            intent = "overtake"
        elif aggression > 0.6:
            intent = "aggressive"
        else:
            intent = "cruise"

        return DriverIntention(
            lane_change_probability=lane_change,
            sudden_brake_probability=brake_prob,
            aggressive_driving_score=aggression,
            unsafe_overtake=overtake,
            primary_intent=intent,
        )
