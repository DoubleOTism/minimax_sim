"""
User-facing texts.

The language is picked once at startup from the MINIMAX_LANG environment variable read in config.py.
Can be `cs` or `en`, default `cs`. Code always uses `texts.NAME`.
"""

from minimax_sim import config

from . import cs, en

LANGUAGES = {"cs": cs, "en": en}

if config.LANG not in LANGUAGES:
    raise ValueError(f"Unknown MINIMAX_LANG {config.LANG!r}, use one of: {', '.join(LANGUAGES)}")
_active = LANGUAGES[config.LANG]


# Forward texts.NAME to the active language module
def __getattr__(name: str) -> str:
    return getattr(_active, name)
