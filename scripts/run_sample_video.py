#!/usr/bin/env python3
"""
Process a sample road video through the full NeuroRoad Sentinel pipeline.
Saves annotated frames + JSON telemetry with all detections.

Usage:
  python scripts/run_sample_video.py
  python scripts/run_sample_video.py --video datasets/videos/road.mp4 --max-frames 120
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai_models.perception.deepsort_tracker import DeepSortTracker
from ai_models.perception.detector import ObjectDetector
from ai_models.perception.encoder import frame_to_base64_jpeg
from ai_models.perception.lane_detection import LaneDetector
from ai_models.perception.monocular_metrics import MonocularMetrics
from ai_models.perception.overlay import OverlayRenderer
from backend.services.pipeline import pipeline

DEFAULT_VIDEO_URL = (
    "https://github.com/intel-iot-devkit/sample-videos/raw/master/car-detection.mp4"
)
OUTPUT_DIR = ROOT / "docs" / "sample_outputs"


def download_sample_video(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100_000:
        print(f"[download] Using cached: {dest}")
        return dest
    print(f"[download] Fetching sample road video...")
    try:
        import urllib.request

        urllib.request.urlretrieve(DEFAULT_VIDEO_URL, dest)
        print(f"[download] Saved: {dest} ({dest.stat().st_size // 1024} KB)")
        return dest
    except Exception as e:
        print(f"[download] Failed: {e}")
        raise


def process_video(video_path: Path, max_frames: int, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[video] {video_path.name} — {w}x{h}, ~{total} frames")

    detector = ObjectDetector(conf=0.4)
    tracker = DeepSortTracker()
    lanes_det = LaneDetector()
    metrics = MonocularMetrics()
    overlay = OverlayRenderer()

    print(f"[ai] YOLO={detector.available}, tracker={tracker.backend}")

    best_frame_data: dict | None = None
    best_det_count = -1
    all_summaries: list[dict] = []
    frame_idx = 0
    processed = 0

    while processed < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        # Sample every 3rd frame for speed
        if frame_idx % 3 != 0:
            continue

        fh, fw = frame.shape[:2]
        detections = detector.detect(frame)
        detections = tracker.update(frame, detections)
        detections = metrics.enrich(detections, (fh, fw))
        lane_lines = lanes_det.detect(frame)

        perception = pipeline.process_frame(
            detections=detections,
            lanes=lane_lines,
            frame_shape=(fh, fw),
            live_mode=True,
        )

        annotated = overlay.render(
            frame,
            detections,
            lane_lines,
            alerts=perception.alerts,
            metadata={**perception.metadata, "tracker": tracker.backend},
        )

        n_det = len(detections)
        summary = {
            "frame_id": perception.frame_id,
            "video_frame": frame_idx,
            "detection_count": n_det,
            "collision_probability": perception.metadata.get("collision_probability"),
            "time_to_collision_sec": perception.metadata.get("time_to_collision_sec"),
            "alerts": [a.model_dump() for a in perception.alerts],
            "detections": [d for d in detections],
            "sensors": perception.sensors.model_dump(),
            "driver_score": perception.driver_score.model_dump(),
            "v2v_count": len(perception.v2v_messages),
        }
        all_summaries.append(summary)

        if n_det > best_det_count:
            best_det_count = n_det
            payload = perception.model_dump()
            payload.pop("camera_frame_jpeg", None)
            best_frame_data = {
                "full_telemetry": payload,
                "detections": detections,
                "lanes": lane_lines,
            }
            best_path = frames_dir / "best_annotated.jpg"
            cv2.imwrite(str(best_path), annotated)
            print(f"  [best] frame {frame_idx}: {n_det} objects, collision={summary['collision_probability']}")

        if processed % 10 == 0 and n_det > 0:
            snap = frames_dir / f"frame_{frame_idx:04d}.jpg"
            cv2.imwrite(str(snap), annotated)

        processed += 1

    cap.release()

    # Write outputs
    report = {
        "video": str(video_path),
        "resolution": [w, h],
        "frames_processed": processed,
        "best_detection_count": best_det_count,
        "tracker": tracker.backend,
        "yolo_active": detector.available,
        "frame_summaries": all_summaries,
    }
    (output_dir / "full_report.json").write_text(json.dumps(report, indent=2))
    if best_frame_data:
        (output_dir / "best_frame_telemetry.json").write_text(
            json.dumps(best_frame_data, indent=2, default=str)
        )

    # HTML gallery for easy viewing
    _write_gallery(output_dir, frames_dir)

    return report


def _write_gallery(output_dir: Path, frames_dir: Path) -> None:
    images = sorted(frames_dir.glob("*.jpg"))
    if not images:
        return
    rows = "\n".join(
        f'<div class="card"><img src="frames/{p.name}"/><p>{p.name}</p></div>'
        for p in images[:20]
    )
    html = f"""<!DOCTYPE html>
<html><head><title>NeuroRoad Sample Outputs</title>
<style>
body {{ background:#0a0e14; color:#e0e0e0; font-family:Inter,sans-serif; padding:24px; }}
h1 {{ color:#00d4aa; }}
.card {{ display:inline-block; margin:12px; background:#111820; border:1px solid #1e2a3a; border-radius:12px; padding:8px; }}
img {{ max-width:420px; border-radius:8px; }}
p {{ font-size:12px; color:#6b7c93; text-align:center; }}
</style></head><body>
<h1>NeuroRoad Sentinel — Sample Road Video Outputs</h1>
{rows}
</body></html>"""
    (output_dir / "gallery.html").write_text(html)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, default=None)
    parser.add_argument("--max-frames", type=int, default=90)
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR))
    args = parser.parse_args()

    video = Path(args.video) if args.video else ROOT / "datasets" / "videos" / "car-detection.mp4"
    if not video.exists():
        video = download_sample_video(video)

    t0 = time.time()
    report = process_video(video, args.max_frames, Path(args.output))
    elapsed = time.time() - t0

    print("\n" + "=" * 60)
    print("DONE — Sample video processing complete")
    print(f"  Output folder: {args.output}")
    print(f"  Best frame detections: {report['best_detection_count']}")
    print(f"  Frames processed: {report['frames_processed']}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Open: {args.output}/gallery.html")
    print(f"  JSON: {args.output}/best_frame_telemetry.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
