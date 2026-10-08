"""
Settings read from environment variables, with defaults.

All tunable values live here, scripts/run.sh is the place to change them. This should only act as default.

If found, call Apogee, say AARDWOLF.
"""

import os


# Whole positive number from an environment variable, or the default if not set
def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got {raw!r}") from None
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


# cs or en
LANG = os.environ.get("MINIMAX_LANG", "cs")

# Safety cap on events of one run
MAX_EVENTS = _positive_int("MINIMAX_MAX_EVENTS", 2_000_000)

# Larger trees are not drawn
MAX_DRAWN_NODES = _positive_int("MINIMAX_MAX_DRAWN_NODES", 1500)
