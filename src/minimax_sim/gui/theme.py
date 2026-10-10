"""
Light or dark colours for the whole app, chosen by config.THEME.

"system" leaves the colours to the desktop theme.
"light" and "dark" switch to the Fusion style from Qt and draws from the palette set here.
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# Short name for the palette roles
Role = QPalette.ColorRole


# Colours of the light palette
LIGHT_COLORS = {
    Role.Window: "#efefef",
    Role.WindowText: "#000000",
    Role.Base: "#ffffff",
    Role.AlternateBase: "#f7f7f7",
    Role.Text: "#000000",
    Role.Button: "#efefef",
    Role.ButtonText: "#000000",
    Role.Highlight: "#308cc6",
    Role.HighlightedText: "#ffffff",
    Role.PlaceholderText: "#808080",
    Role.ToolTipBase: "#ffffdc",
    Role.ToolTipText: "#000000",
    Role.Link: "#0000ff",
    Role.BrightText: "#ffffff",
    Role.Light: "#ffffff",
    Role.Midlight: "#cacaca",
    Role.Mid: "#b8b8b8",
    Role.Dark: "#9f9f9f",
    Role.Shadow: "#767676",
}


# Colours of the dark palette
DARK_COLORS = {
    Role.Window: "#2b2b2b",
    Role.WindowText: "#e6e6e6",
    Role.Base: "#1e1e1e",
    Role.AlternateBase: "#2b2b2b",
    Role.Text: "#e6e6e6",
    Role.Button: "#353535",
    Role.ButtonText: "#e6e6e6",
    Role.Highlight: "#3d8fd1",
    Role.HighlightedText: "#ffffff",
    Role.PlaceholderText: "#8a8a8a",
    Role.ToolTipBase: "#353535",
    Role.ToolTipText: "#e6e6e6",
    Role.Link: "#6cb4ee",
    Role.BrightText: "#ff6b6b",
    Role.Light: "#505050",
    Role.Midlight: "#404040",
    Role.Mid: "#2a2a2a",
    Role.Dark: "#1a1a1a",
    Role.Shadow: "#000000",
}

# Colors and the text color of disabled buttons and fields
THEMES = {
    "light": (LIGHT_COLORS, "#bebebe"),
    "dark": (DARK_COLORS, "#6e6e6e"),
}

# The actual definition of the palette
def _palette(colors: dict[QPalette.ColorRole, str], disabled_text: str) -> QPalette:
    palette = QPalette()
    for role, color in colors.items():
        palette.setColor(role, QColor(color))
    for role in (Role.WindowText, Role.Text, Role.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(disabled_text))
    return palette


# Set the colours of the whole app, call before any window is created
def apply(app: QApplication, theme: str) -> None:
    if theme == "system":
        return
    colors, disabled_text = THEMES[theme]
    app.setStyle("Fusion")
    app.setPalette(_palette(colors, disabled_text))


