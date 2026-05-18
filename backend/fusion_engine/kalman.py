"""Kalman filter for multi-sensor state estimation (position, velocity)."""

import numpy as np
from filterpy.kalman import KalmanFilter


class VehicleStateKalman:
    """4D state: [x, y, vx, vy] with constant-velocity model."""

    def __init__(self, dt: float = 0.1):
        self.dt = dt
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        self.kf.x = np.array([0.0, 0.0, 0.0, 0.0])
        self.kf.F = np.array(
            [
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ]
        )
        self.kf.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        self.kf.P *= 500.0
        self.kf.R = np.eye(2) * 2.0
        self.kf.Q = np.eye(4) * 0.05
        self._initialized = False

    def predict(self) -> np.ndarray:
        self.kf.predict()
        return self.kf.x.copy()

    def update(self, measurement: tuple[float, float]) -> np.ndarray:
        z = np.array([measurement[0], measurement[1]])
        if not self._initialized:
            self.kf.x[0], self.kf.x[1] = z[0], z[1]
            self._initialized = True
        self.kf.update(z)
        return self.kf.x.copy()

    @property
    def position(self) -> tuple[float, float]:
        return float(self.kf.x[0]), float(self.kf.x[1])

    @property
    def velocity(self) -> tuple[float, float]:
        return float(self.kf.x[2]), float(self.kf.x[3])
