"""Render ADAS overlays: boxes, lanes, TTC, trajectories, alerts."""

from __future__ import annotations

import cv2
import numpy as np

COLOR_VEHICLE = (255, 140, 0)
COLOR_PERSON = (0, 100, 255)
COLOR_LANE = (0, 255, 160)
COLOR_TRAJ = (0, 212, 170)
COLOR_ALERT = (71, 71, 255)
COLOR_TTC_WARN = (0, 180, 255)
COLOR_TTC_CRIT = (71, 71, 255)


class OverlayRenderer:
    def render(
        self,
        frame: np.ndarray,
        detections: list[dict],
        lanes: list[list[tuple[float, float]]],
        alerts: list | None = None,
        metadata: dict | None = None,
    ) -> np.ndarray:
        out = frame.copy()
        h, w = out.shape[:2]

        for lane in lanes:
            pts = np.array(lane, dtype=np.int32)
            if len(pts) >= 2:
                cv2.polylines(out, [pts], False, COLOR_LANE, 3, cv2.LINE_AA)

        for det in detections:
            x1, y1, x2, y2 = map(int, [det["x1"], det["y1"], det["x2"], det["y2"]])
            is_person = det.get("class_name") == "person"
            color = COLOR_PERSON if is_person else COLOR_VEHICLE
            ttc = det.get("ttc_sec")
            col_p = det.get("collision_probability", 0)
            if ttc is not None and ttc < 2.0:
                color = COLOR_TTC_CRIT
            elif ttc is not None and ttc < 4.0:
                color = COLOR_TTC_WARN

            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            tid = det.get("track_id", "?")
            dist = det.get("distance_m")
            vel = det.get("velocity_ms")
            lines = [
                f"{det['class_name']} ID:{tid} {det['confidence']:.2f}",
            ]
            if dist is not None:
                lines.append(f"D:{dist:.1f}m V:{vel:.1f}m/s")
            if ttc is not None:
                lines.append(f"TTC:{ttc:.1f}s P:{col_p:.0%}")
            for i, line in enumerate(lines):
                cv2.putText(
                    out,
                    line,
                    (x1, max(y1 - 8 - i * 18, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    color,
                    1,
                    cv2.LINE_AA,
                )

        # HUD
        meta = metadata or {}
        col_prob = meta.get("collision_probability", 0)
        ttc_global = meta.get("time_to_collision_sec")
        input_type = meta.get("input_type", "webcam")
        input_name = meta.get("input_source", "")
        mode = f"VIDEO: {input_name}" if input_type == "video" else "LIVE AI"
        hud = [
            f"NeuroRoad Sentinel | {mode}",
            f"Collision: {col_prob:.0%}" + (f" | TTC: {ttc_global:.1f}s" if ttc_global else ""),
            f"Tracks: {len(detections)} | {meta.get('tracker', 'deepsort')}",
        ]
        for i, line in enumerate(hud):
            cv2.putText(
                out,
                line,
                (12, 28 + i * 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (220, 220, 220),
                2,
                cv2.LINE_AA,
            )

        if alerts:
            y0 = h - 20
            for alert in alerts[:2]:
                msg = alert.message if hasattr(alert, "message") else alert.get("message", "")
                level = alert.level.value if hasattr(alert, "level") else alert.get("level", "info")
                c = COLOR_ALERT if level == "critical" else COLOR_TTC_WARN
                cv2.putText(out, msg, (12, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.55, c, 2, cv2.LINE_AA)
                y0 -= 28

        return out
