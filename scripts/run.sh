#!/usr/bin/env sh

# Start the simulator.
# Uncomment and change a value to tune it.
# Defaults are in src/minimax_sim/config.py.
# Usage: ./scripts/run.sh [arguments for the app]

set -eu
cd "$(dirname "$0")/.."

# Language, cs or en
# export MINIMAX_LANG=en

# Safety cap on events of one run
# export MINIMAX_MAX_EVENTS=2000000

# Trees with more nodes than this are not drawn
# export MINIMAX_MAX_DRAWN_NODES=1500

exec .venv/bin/python -m minimax_sim "$@"