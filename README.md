# NeuroRoad Sentinel

**AI-Powered Cooperative ADAS & Autonomous Risk Prediction System**

Real-time cooperative AI platform for predictive autonomous driving safety. Unlike traditional ADAS that only detects present obstacles, NeuroRoad Sentinel performs **future-risk intelligence** using sensor fusion, computer vision, trajectory prediction, and explainable decision assistance.

![Stack](https://img.shields.io/badge/Python-3.11+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green) ![React](https://img.shields.io/badge/React-18-61dafb) ![YOLOv8](https://img.shields.io/badge/YOLOv8-ultralytics-orange)

## Features

| Module | Capability |
|--------|------------|=
| **Multi-Camera Perception** | Vehicle, pedestrian, lane, sign detection + blind-spot analysis |
| **Driver Intention** | Lane-change, braking, aggressive driving prediction |
| **Collision Forecasting** | 3–5s collision probability, trajectory overlap, risk heatmaps |
| **Sensor Fusion** | Camera + radar/GPS/IMU simulation with Kalman filtering |
| **Decision Engine** | Brake, slow-down, lane correction, collision avoidance alerts |
| **Digital Twin Dashboard** | Live 3D surroundings, risk map, predicted paths, driver score |
| **V2V Simulation** | Cooperative vehicle intelligence & sudden-brake alerts |
| **Explainable AI** | Human-readable reasoning for every warning |

## Architecture

```
Camera / GPS / IMU / Radar (sim)
        ↓
   Perception (YOLOv8, lanes, tracking)
        ↓
   Fusion (Kalman, temporal sync)
        ↓
   Intelligence (LSTM trajectories, risk classifier)
        ↓
   Decision (alerts, recommendations)
        ↓
   Digital Twin Dashboard (WebSocket)
```

## Tech Stack

- **Frontend:** React, Tailwind CSS, Framer Motion, Three.js, Chart.js
- **Backend:** FastAPI, WebSockets
- **AI/ML:** PyTorch, YOLOv8, OpenCV, scikit-learn, filterpy
- **Simulation:** CARLA, SUMO (integration stubs)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Webcam (optional — demo mode works without hardware)

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r ../requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** for the Digital Twin dashboard.

**Live AI runs inside the backend** — on startup it automatically:
- Opens your webcam (OpenCV)
- Runs YOLOv8 vehicle/pedestrian detection
- Tracks objects with DeepSORT
- Detects lanes, estimates distance/velocity/TTC
- Streams annotated video + telemetry over WebSocket

Grant **camera permission** when prompted (macOS: System Settings → Privacy → Camera).

### Live road video demo (screen recording)

Use a sample driving video instead of your webcam — loops continuously for portfolio recordings:

```bash
bash scripts/start_video_demo.sh                    # vehicle-counting (default)
bash scripts/start_video_demo.sh car-detection      # parking / close-range cars
```

Then open **http://127.0.0.1:5173** and screen-record the dashboard.

Optional standalone runner:
```bash
python ai_models/run_detection.py --source 0
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Project Structure

```
NeuroRoad-Sentinel/
├── frontend/          # React digital twin dashboard
├── backend/           # FastAPI + WebSocket + engines
├── ai_models/         # YOLOv8, tracking, LSTM, risk ML
├── simulation/        # CARLA & SUMO integration
├── docker/
├── notebooks/
└── datasets/
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | System health |
| `GET /api/telemetry` | Latest fused telemetry |
| `GET /api/risk` | Current risk assessment |
| `GET /api/driver-score` | Driver behavior score |
| `WS /ws/stream` | Real-time perception + risk stream |

## Interview Pitch

> I developed an AI-powered cooperative ADAS system that predicts future driving risks using sensor fusion, computer vision, and trajectory prediction. Unlike traditional ADAS that only detect present obstacles, my system performs predictive intelligence and autonomous decision assistance using multi-modal data.

## Datasets (May built in future)

- **Detection:** BDD100K, KITTI, COCO
- **Lanes:** TuSimple
- **Autonomous:** nuScenes, Waymo Open
- **Driver behavior:** State Farm

## License

MIT — built for portfolio & research use.
# NeuroRoad-Sentinel
# NeuroRoad-Sentinel
# NeuroRoad-Sentinel
