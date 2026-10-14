#!/usr/bin/env sh

# Start the simulator.
# Uncomment and change a value to tune it.
# Defaults are in src/minimax_sim/config.py.
#
# Usage:
#   ./scripts/run.sh [arguments for the app]           Python and PySide6 from .venv, made by scripts/setup.sh
#   ./scripts/run.sh --system [arguments for the app]  system Python with PySide6 from the distribution

set -eu
cd "$(dirname "$0")/.."

# Language, cs or en
# export MINIMAX_LANG=en

# Safety cap on events of one run
# export MINIMAX_MAX_EVENTS=2000000

# Trees with more nodes than this are not drawn
# export MINIMAX_MAX_DRAWN_NODES=1500

# How the window opens: window, maximized or fullscreen
# export MINIMAX_WINDOW_MODE=maximized

# Part of the screen a normal window takes, 0.8 = 80 %
# export MINIMAX_WINDOW_SCALE=0.8

# Colour themes: system, light, or dark
# export MINIMAX_THEME=dark

# System Python, the project is not installed, so Python looks for it in src/
if [ "${1:-}" = "--system" ]; then
    shift
    if ! python3 -c "import PySide6" 2>/dev/null; then
        echo "Systémový Python nemá PySide6. Na Archu: sudo pacman -S pyside6" >&2
        exit 1
    fi
    export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
    exec python3 -m minimax_sim "$@"
fi

# Python from .venv, the project is installed there by scripts/setup.sh
if [ ! -x .venv/bin/python ]; then
    echo "Chybí .venv. Spusťte sh scripts/setup.sh, nebo ./scripts/run.sh --system" >&2
    exit 1
fi
exec .venv/bin/python -m minimax_sim "$@"