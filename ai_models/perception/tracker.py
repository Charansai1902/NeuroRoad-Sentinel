"""DeepSORT-style simple IoU tracker (lightweight, no extra deps)."""

from __future__ import annotations


def _iou(a: dict, b: dict) -> float:
    x1 = max(a["x1"], b["x1"])
    y1 = max(a["y1"], b["y1"])
    x2 = min(a["x2"], b["x2"])
    y2 = min(a["y2"], b["y2"])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
    area_b = (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
    union = area_a + area_b - inter + 1e-6
    return inter / union


class SimpleTracker:
    def __init__(self, iou_threshold: float = 0.3, max_age: int = 30):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self._tracks: dict[int, dict] = {}
        self._next_id = 1

    def update(self, detections: list[dict]) -> list[dict]:
        if not self._tracks:
            for det in detections:
                tid = self._next_id
                self._next_id += 1
                det["track_id"] = tid
                self._tracks[tid] = {**det, "age": 0}
            return detections

        matched = set()
        for det in detections:
            best_iou, best_id = 0.0, None
            for tid, track in self._tracks.items():
                if tid in matched:
                    continue
                iou = _iou(det, track)
                if iou > self.iou_threshold and iou > best_iou:
                    best_iou, best_id = iou, tid
            if best_id is not None:
                det["track_id"] = best_id
                self._tracks[best_id] = {**det, "age": 0}
                matched.add(best_id)
            else:
                tid = self._next_id
                self._next_id += 1
                det["track_id"] = tid
                self._tracks[tid] = {**det, "age": 0}

        for tid in list(self._tracks):
            if tid not in matched:
                self._tracks[tid]["age"] = self._tracks[tid].get("age", 0) + 1
                if self._tracks[tid]["age"] > self.max_age:
                    del self._tracks[tid]

        return detections
