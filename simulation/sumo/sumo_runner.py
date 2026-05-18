"""
SUMO traffic simulation stub.
Requires SUMO installed: https://eclipse.dev/sumo/

Usage:
  python simulation/sumo/sumo_runner.py --config simulation/sumo/scenario.sumocfg
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="SUMO runner for NeuroRoad Sentinel")
    parser.add_argument("--config", type=str, default="simulation/sumo/scenario.sumocfg")
    args = parser.parse_args()

    cfg = Path(args.config)
    if not cfg.exists():
        print(f"[SUMO] Config not found: {cfg}")
        print("[SUMO] Create a .sumocfg and network files, or use CARLA demo mode.")
        sys.exit(1)

    try:
        subprocess.run(["sumo-gui", "-c", str(cfg)], check=True)
    except FileNotFoundError:
        print("[SUMO] sumo-gui not in PATH. Install SUMO and retry.")
        sys.exit(1)


if __name__ == "__main__":
    main()
