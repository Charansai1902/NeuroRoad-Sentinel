#!/usr/bin/env bash
# Start NeuroRoad Sentinel with LIVE sample road video on the dashboard (for screen recording)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIDEO_NAME="${1:-road-traffic}"
VIDEO_PATH="$ROOT/datasets/videos/${VIDEO_NAME}.mp4"

cd "$ROOT"
bash scripts/download_demo_videos.sh

if [[ ! -f "$VIDEO_PATH" ]]; then
  echo "Video not found: $VIDEO_PATH"
  echo "Available: car-detection, road-traffic"
  exit 1
fi

export PYTHONPATH="$ROOT"
export CAMERA_SOURCE="$VIDEO_PATH"
export VIDEO_LOOP=true
export PERCEPTION_ENABLED=true
export DEMO_MODE=false
export TARGET_FPS=15
export JPEG_QUALITY=80

echo ""
echo "════════════════════════════════════════════════════════"
echo "  NeuroRoad Sentinel — LIVE VIDEO DEMO"
echo "  Input: $VIDEO_PATH"
echo "  Dashboard: http://127.0.0.1:5173"
echo "  API:       http://127.0.0.1:8000/docs"
echo ""
echo "  Screen record the dashboard in fullscreen for your portfolio."
echo "  Press Ctrl+C to stop."
echo "════════════════════════════════════════════════════════"
echo ""

# Stop old servers
pkill -f "uvicorn backend.main:app" 2>/dev/null || true
pkill -f "vite.*5173" 2>/dev/null || true
sleep 1

source "$ROOT/backend/.venv/bin/activate"

# Backend
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACK_PID=$!
sleep 4

# Frontend
cd "$ROOT/frontend"
npm run dev -- --host 127.0.0.1 &
FRONT_PID=$!

trap "kill $BACK_PID $FRONT_PID 2>/dev/null; exit" INT TERM

echo "Backend PID: $BACK_PID | Frontend PID: $FRONT_PID"
wait
