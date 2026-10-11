#!/bin/bash
# RogueByte GeoForensics Intelligence - Linux / macOS Local Runner
set -e

echo "======================================================================"
echo "  RogueByte GeoForensics Intelligence - التشغيل المحلي (Linux/macOS)"
echo "======================================================================"

python3 --version || { echo "Python3 not found"; exit 1; }

if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment (venv)..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "[*] Launching RogueByte..."
python3 main.py "$@"
