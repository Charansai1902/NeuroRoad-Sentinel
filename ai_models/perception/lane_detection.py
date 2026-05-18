"""Lane detection via OpenCV edge + Hough lines (UFLD-ready stub)."""

from __future__ import annotations

import cv2
import numpy as np


class LaneDetector:
    def detect(self, frame: np.ndarray) -> list[list[tuple[float, float]]]:
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        mask = np.zeros_like(edges)
        roi = np.array(
            [[(0, h), (w, h), (int(w * 0.55), int(h * 0.55)), (int(w * 0.45), int(h * 0.55))]],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, roi, 255)
        masked = cv2.bitwise_and(edges, mask)

        lines = cv2.HoughLinesP(
            masked, 1, np.pi / 180, 50, minLineLength=40, maxLineGap=100
        )

        left_pts, right_pts = [], []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cx = (x1 + x2) / 2
                if cx < w * 0.5:
                    left_pts.append((float(x1), float(y1)))
                    left_pts.append((float(x2), float(y2)))
                else:
                    right_pts.append((float(x1), float(y1)))
                    right_pts.append((float(x2), float(y2)))

        if len(left_pts) < 2:
            left_pts = [(w * 0.35, h), (w * 0.4, h * 0.55)]
        if len(right_pts) < 2:
            right_pts = [(w * 0.65, h * 0.55), (w * 0.7, h)]

        return [left_pts, right_pts]
