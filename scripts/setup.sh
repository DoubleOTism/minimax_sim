#!/usr/bin/env sh

# Create .venv and install the project (editable) with dev tools.
# Usage: sh scripts/setup.sh [python]   (default: python3)
set -eu
cd "$(dirname "$0")/.."
PY="${1:-python3}"

"$PY" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"

echo
if ls .venv/lib/python*/site-packages/PySide6/Qt/plugins/platforms/ 2>/dev/null | grep -q wayland; then
    echo "Wayland plugin found"
else
    echo "Wayland plugin not found, the app will run through XWayland"
fi
echo "Done"
