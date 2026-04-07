#!/bin/bash
# Build PDF Merger for macOS — delegates to build.py
set -e

VENV_PYTHON=".venv/bin/python"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: .venv not found. Run: python -m venv .venv && .venv/bin/pip install -r requirements.txt pyinstaller"
    exit 1
fi

"$VENV_PYTHON" build.py macos
