"""Explainable AI — human-readable reasoning for ADAS warnings."""

from backend.api.schemas import ExplainableReason


def build_explanation(
    collision_probability: float,
    factors: list[str],
    ttc_sec: float | None = None,
) -> ExplainableReason:
    if collision_probability >= 0.8:
        summary = "Critical collision risk detected."
    elif collision_probability >= 0.5:
        summary = "Elevated collision probability — caution advised."
    elif collision_probability >= 0.3:
        summary = "Moderate risk — monitor surrounding traffic."
    else:
        summary = "Road conditions within normal risk parameters."

    if ttc_sec is not None and ttc_sec < 3.0:
        summary += f" Estimated time-to-collision: {ttc_sec:.1f}s."

    confidence = min(0.99, 0.5 + collision_probability * 0.45)
    return ExplainableReason(summary=summary, factors=factors, confidence=confidence)
