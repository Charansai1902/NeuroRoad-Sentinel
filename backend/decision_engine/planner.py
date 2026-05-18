"""Autonomous decision layer — prioritizes alerts and recommendations."""

from backend.api.schemas import Alert, AlertAction, AlertLevel


class DecisionEngine:
  PRIORITY = {
    AlertAction.BRAKE: 0,
    AlertAction.COLLISION_AVOID: 1,
    AlertAction.SLOW_DOWN: 2,
    AlertAction.LANE_CORRECT: 3,
    AlertAction.BLIND_SPOT: 4,
    AlertAction.DRIVER_WARNING: 5,
    AlertAction.NONE: 99,
  }

  def prioritize(self, alerts: list[Alert]) -> list[Alert]:
    return sorted(
      alerts,
      key=lambda a: (
        self.PRIORITY.get(a.action, 50),
        -a.collision_probability,
      ),
    )

  def top_recommendation(self, alerts: list[Alert]) -> Alert | None:
    ordered = self.prioritize(alerts)
    return ordered[0] if ordered else None

  def blind_spot_alert(self, left_m: float, right_m: float) -> Alert | None:
    from backend.api.schemas import ExplainableReason

    if left_m < 5:
      return Alert(
        level=AlertLevel.WARNING,
        action=AlertAction.BLIND_SPOT,
        message="Vehicle in left blind spot",
        explanation=ExplainableReason(
          summary="Left blind spot occupancy detected",
          factors=[f"Left radar: {left_m:.1f}m"],
          confidence=0.85,
        ),
        collision_probability=0.4,
      )
    if right_m < 5:
      return Alert(
        level=AlertLevel.WARNING,
        action=AlertAction.BLIND_SPOT,
        message="Vehicle in right blind spot",
        explanation=ExplainableReason(
          summary="Right blind spot occupancy detected",
          factors=[f"Right radar: {right_m:.1f}m"],
          confidence=0.85,
        ),
        collision_probability=0.4,
      )
    return None
