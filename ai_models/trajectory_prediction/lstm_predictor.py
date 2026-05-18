"""LSTM trajectory predictor (trainable; demo uses kinematic extrapolation)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

try:
    import torch
    import torch.nn as nn
except ImportError:
    torch = None  # type: ignore
    nn = None  # type: ignore


@dataclass
class PredictedPath:
    track_id: int
    points: list[tuple[float, float, float]]  # t, x, y


class TrajectoryLSTM(nn.Module if nn else object):  # type: ignore
    """Sequence-to-sequence LSTM for (x,y) prediction."""

    def __init__(self, input_dim: int = 4, hidden: int = 64, horizon: int = 10):
        if nn is None:
            return
        super().__init__()
        self.horizon = horizon
        self.lstm = nn.LSTM(input_dim, hidden, batch_first=True)
        self.fc = nn.Linear(hidden, 2)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


class TrajectoryPredictor:
    HORIZON = 5.0
    STEPS = 10

    def __init__(self):
        self._model = None
        if torch is not None and nn is not None:
            self._model = TrajectoryLSTM()
            self._model.eval()

    def predict(
        self,
        track_id: int,
        history: list[tuple[float, float]],
        velocity: tuple[float, float] = (0.0, 0.0),
    ) -> PredictedPath:
        if len(history) >= 2:
            vx = history[-1][0] - history[-2][0]
            vy = history[-1][1] - history[-2][1]
        else:
            vx, vy = velocity

        x0, y0 = history[-1] if history else (0.0, 0.0)
        points = []
        dt = self.HORIZON / self.STEPS
        for i in range(self.STEPS + 1):
            t = i * dt
            points.append((t, x0 + vx * t * 10, y0 + vy * t * 10))
        return PredictedPath(track_id=track_id, points=points)
