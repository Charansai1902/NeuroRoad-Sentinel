"""
CARLA simulator integration stub.
Install CARLA 0.9.x and set CARLA_ROOT to enable full integration.

Usage:
  python simulation/carla/carla_simulation.py --host localhost --port 2000
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="CARLA integration for NeuroRoad Sentinel")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    args = parser.parse_args()

    try:
        import carla  # type: ignore
    except ImportError:
        print(
            "[CARLA] Python API not installed.\n"
            "  1. Download CARLA from https://carla.org\n"
            "  2. pip install carla/dist/carla-*.whl\n"
            "  3. Start CarlaUE4.sh then re-run this script"
        )
        sys.exit(1)

    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    world = client.get_world()
    print(f"[CARLA] Connected to {world.get_map().name}")
    print("[CARLA] Spawn ego + sensors — extend this module for full ADAS loop")


if __name__ == "__main__":
    main()
