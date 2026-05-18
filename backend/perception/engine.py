"""Live perception engine: webcam → YOLOv8 → DeepSORT → lanes → risk → stream."""

from __future__ import annotations

import logging
import threading
import time

from ai_models.perception.deepsort_tracker import DeepSortTracker
from ai_models.perception.detector import ObjectDetector
from ai_models.perception.encoder import frame_to_base64_jpeg
from ai_models.perception.lane_detection import LaneDetector
from ai_models.perception.monocular_metrics import MonocularMetrics
from ai_models.perception.overlay import OverlayRenderer
from backend.config import settings
from backend.perception.camera import CameraStream
from backend.perception.frame_hub import frame_hub
from backend.services.pipeline import pipeline

logger = logging.getLogger(__name__)


class PerceptionEngine:
    def __init__(self):
        self.camera = CameraStream(
            source=settings.camera_source,
            width=settings.camera_width,
            height=settings.camera_height,
            fps=settings.camera_fps,
            loop_video=settings.video_loop,
        )
        self.detector = ObjectDetector(
            model_name=settings.yolo_model,
            conf=settings.yolo_conf,
        )
        self.tracker = DeepSortTracker(max_age=settings.track_max_age)
        self.lanes = LaneDetector()
        self.metrics = MonocularMetrics(focal_scale=settings.focal_scale)
        self.overlay = OverlayRenderer()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._frame_times: list[float] = []

    @property
    def status(self) -> dict:
        return {
            "running": frame_hub.is_running,
            "camera": self.camera.is_open,
            "yolo": self.detector.available,
            "tracker": self.tracker.backend,
            "has_frame": frame_hub.has_frame,
            "input": self.camera.input_label,
            "input_type": "video" if self.camera.is_video_file else "webcam",
        }

    def start(self) -> bool:
        if self._thread and self._thread.is_alive():
            return True
        if not self.camera.open():
            logger.warning("Webcam unavailable — perception loop will retry")
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="perception-engine", daemon=True)
        self._thread.start()
        frame_hub.set_running(True)
        logger.info(
            "Perception engine started (YOLO=%s, tracker=%s)",
            self.detector.available,
            self.tracker.backend,
        )
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        self.camera.release()
        frame_hub.set_running(False)
        logger.info("Perception engine stopped")

    def _throttle(self) -> None:
        target = 1.0 / max(settings.target_fps, 1)
        if self._frame_times:
            elapsed = time.time() - self._frame_times[-1]
            sleep = target - elapsed
            if sleep > 0:
                time.sleep(sleep)
        self._frame_times.append(time.time())
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)

    def _loop(self) -> None:
        while not self._stop.is_set():
            if not self.camera.is_open:
                if not self.camera.open():
                    time.sleep(1.0)
                    continue

            ok, frame = self.camera.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue

            try:
                self._process(frame)
            except Exception:
                logger.exception("Perception frame error")
            self._throttle()

    def _process(self, frame) -> None:
        h, w = frame.shape[:2]
        detections = self.detector.detect(frame)
        detections = self.tracker.update(frame, detections)
        detections = self.metrics.enrich(detections, (h, w))
        lane_lines = self.lanes.detect(frame)

        perception = pipeline.process_frame(
            detections=detections,
            lanes=lane_lines,
            frame_shape=(h, w),
            live_mode=True,
        )

        annotated = self.overlay.render(
            frame,
            detections,
            lane_lines,
            alerts=perception.alerts,
            metadata={
                **perception.metadata,
                "tracker": self.tracker.backend,
            },
        )
        jpeg_b64 = frame_to_base64_jpeg(annotated, quality=settings.jpeg_quality)

        perception.camera_frame_jpeg = jpeg_b64
        perception.live_mode = True
        perception.metadata["tracker"] = self.tracker.backend
        perception.metadata["yolo_active"] = self.detector.available
        perception.metadata["input_source"] = self.camera.input_label
        perception.metadata["input_type"] = "video" if self.camera.is_video_file else "webcam"

        frame_hub.update(perception)


perception_engine = PerceptionEngine()
