"""
Small "?" button with an explanation, used in the side panels of both tabs.
"""

from PySide6.QtWidgets import QToolButton, QToolTip


# Button with an explanation, shown on hover and also on click
# The click shows the current tooltip text, so a later setToolTip() changes the text on hover and on click
def help_button(text: str) -> QToolButton:
    button = QToolButton()
    button.setText("?")
    button.setToolTip(text)
    button.clicked.connect(
        lambda: QToolTip.showText(button.mapToGlobal(button.rect().bottomLeft()), button.toolTip(), button)
    )
    return button
