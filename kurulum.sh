#!/usr/bin/env bash
# Linux / macOS kurulumu
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
$PY -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q -m "not slow"
python scripts/generate_sample.py --duration 30
echo "Kurulum tamam. Etkinleştirmek için: source .venv/bin/activate"
