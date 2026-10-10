"""
The actual app entry point.

Launched by scripts/run.sh, or directly with python -m minimax_sim
"""

import sys

import PySide6
from PySide6.QtWidgets import QApplication

from minimax_sim import config
from minimax_sim.gui import theme
from minimax_sim.gui.main_window import MainWindow


# Start the Qt application and show the main window
def main() -> int:
    app = QApplication(sys.argv)
    app.setDesktopFileName("minimax-sim")
    theme.apply(app, config.THEME)

    # Which display backend Qt picked, useful when something looks wrong.
    print(
        f"Qt platform: {app.platformName()}, PySide6 {PySide6.__version__}, "
        f"theme {config.THEME}, style {app.style().name()}",
        file=sys.stderr,
    )

    window = MainWindow()
    window.show_by_config()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())