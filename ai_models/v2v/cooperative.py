"""V2V cooperative intelligence — shares risk between simulated agents."""

from dataclasses import dataclass


@dataclass
class CooperativeAlert:
    source_id: str
    alert_type: str
    message: str
    risk_level: float


class CooperativeIntelligence:
    def process_messages(self, messages: list[dict]) -> list[CooperativeAlert]:
        alerts = []
        for msg in messages:
            if msg.get("sudden_brake"):
                alerts.append(
                    CooperativeAlert(
                        source_id=msg["vehicle_id"],
                        alert_type="sudden_brake",
                        message=f"{msg['vehicle_id']} reported emergency braking",
                        risk_level=msg.get("risk_level", 0.7),
                    )
                )
            if msg.get("risk_level", 0) > 0.75:
                alerts.append(
                    CooperativeAlert(
                        source_id=msg["vehicle_id"],
                        alert_type="high_risk_neighbor",
                        message=f"High risk vehicle nearby: {msg['vehicle_id']}",
                        risk_level=msg["risk_level"],
                    )
                )
        return alerts
