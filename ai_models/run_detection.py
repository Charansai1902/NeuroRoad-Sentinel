#!/usr/bin/env python3
"""Standalone perception runner (optional — production uses backend perception engine)."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import settings
from backend.perception.engine import PerceptionEngine


def main():
    parser = argparse.ArgumentParser(description="NeuroRoad Sentinel — standalone perception")
    parser.add_argument("--source", default=None, help="Camera index or video path")
    args = parser.parse_args()

    if args.source is not None:
        settings.camera_source = int(args.source) if str(args.source).isdigit() else args.source

    engine = PerceptionEngine()
    print("[NeuroRoad] Starting standalone perception. Press Ctrl+C to stop.")
    engine.start()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()


if __name__ == "__main__":
    main()
