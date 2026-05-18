#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="${PWD}:${PYTHONPATH}"
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
