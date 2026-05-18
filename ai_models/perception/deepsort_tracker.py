"""DeepSORT multi-object tracking via deep-sort-realtime."""

from __future__ import annotations

import numpy as np

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except ImportError:
    DeepSort = None  # type: ignore

from ai_models.perception.tracker import SimpleTracker


class DeepSortTracker:
    """Production tracker with IoU fallback when DeepSORT unavailable."""

    def __init__(self, max_age: int = 30):
        self._fallback = SimpleTracker(iou_threshold=0.35, max_age=max_age)
        self._deepsort = None
        if DeepSort is not None:
            try:
                self._deepsort = DeepSort(
                    max_age=max_age,
                    n_init=2,
                    nms_max_overlap=0.85,
                    max_cosine_distance=0.35,
                    embedder="mobilenet",
                    half=True,
                    embedder_gpu=False,
                    bgr=True,
                )
            except Exception:
                self._deepsort = None

    @property
    def backend(self) -> str:
        return "deepsort" if self._deepsort else "iou_fallback"

    def update(self, frame: np.ndarray, detections: list[dict]) -> list[dict]:
        if not detections:
            return []

        if self._deepsort is None:
            return self._fallback.update(detections)

        bbs = [
            (
                [d["x1"], d["y1"], d["x2"], d["y2"]],
                d["confidence"],
                d["class_name"],
            )
            for d in detections
        ]
        tracks = self._deepsort.update_tracks(bbs, frame=frame)
        tracked: list[dict] = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            tid = track.track_id
            ltrb = track.to_ltrb()
            cls = track.get_det_class() or "car"
            conf = track.get_det_conf() or 0.5
            tracked.append(
                {
                    "x1": float(ltrb[0]),
                    "y1": float(ltrb[1]),
                    "x2": float(ltrb[2]),
                    "y2": float(ltrb[3]),
                    "confidence": float(conf),
                    "class_name": cls,
                    "track_id": int(tid),
                }
            )
        return tracked
