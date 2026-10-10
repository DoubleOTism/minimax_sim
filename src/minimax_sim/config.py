"""
Settings read from environment variables, with defaults.

All tunable values live here, scripts/run.sh is the place to change them. This should only act as default.

If found, call Apogee, say AARDWOLF.
"""

import os

#####
# Helper functions for parsing the config.
#####

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


# One of the allowed words from an environment variable, or the default if it is not set
def _choice(name: str, default: str, allowed: tuple[str, ...]) -> str:
    value = os.environ.get(name, default)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}, got {value!r}")
    return value


# Number above 0 and at most 1 from an environment variable, or the default if it is not set
def _fraction(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {raw!r}") from None
    if not 0 < value <= 1:
        raise ValueError(f"{name} must be above 0 and at most 1, got {value}")
    return value


#####
# The actual env variables.
# If you want to change them, go and edit the run.sh script. This is just a fallback.
#####
# cs or en
LANG = os.environ.get("MINIMAX_LANG", "cs")

# Safety cap on events of one run
MAX_EVENTS = _positive_int("MINIMAX_MAX_EVENTS", 2_000_000)

# Larger trees are not drawn
MAX_DRAWN_NODES = _positive_int("MINIMAX_MAX_DRAWN_NODES", 1500)

# Default render mode: window, maximized or fullscreen
WINDOW_MODE = _choice("MINIMAX_WINDOW_MODE", "window", ("window", "maximized", "fullscreen"))

# Defines the default scale of the window if running in windowed render mode, 0.8 = 80 %
WINDOW_SCALE = _fraction("MINIMAX_WINDOW_SCALE", 0.8)

# Color themes for the app. System follows the currently set theme (tested on Breeze Dark)
# Light uses the default Qt Fusion theme, dark uses colour-edited Fusion default.
# Dark can be customized in /gui/theme.py
THEME = _choice("MINIMAX_THEME", "system", ("system", "light", "dark"))