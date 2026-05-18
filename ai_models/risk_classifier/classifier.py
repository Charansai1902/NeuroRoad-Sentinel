"""Risk classification using Random Forest features (sklearn)."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier


class RiskClassifier:
    """Classifies frame risk level: low / medium / high."""

    LABELS = ["low", "medium", "high"]

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
        self._fit_demo()

    def _fit_demo(self):
        # Synthetic training data: [speed, front_dist, num_objects, max_det_conf]
        X = np.array(
            [
                [30, 80, 1, 0.7],
                [50, 40, 2, 0.8],
                [70, 25, 3, 0.85],
                [90, 15, 2, 0.9],
                [100, 8, 4, 0.92],
                [40, 60, 1, 0.6],
                [55, 35, 2, 0.75],
            ]
        )
        y = np.array([0, 0, 1, 1, 2, 0, 1])
        self.model.fit(X, y)

    def predict(
        self,
        speed_kmh: float,
        front_distance_m: float,
        num_objects: int,
        max_confidence: float,
    ) -> tuple[str, float]:
        X = np.array([[speed_kmh, front_distance_m, num_objects, max_confidence]])
        proba = self.model.predict_proba(X)[0]
        idx = int(np.argmax(proba))
        return self.LABELS[idx], float(proba[idx])
