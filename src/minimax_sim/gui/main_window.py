"""
Main application window.
"""

from PySide6.QtWidgets import QMainWindow

from minimax_sim import config, presets, texts
from minimax_sim.core.games.abstract_tree import AbstractTree
from minimax_sim.gui.tree_view import TreeView
from minimax_sim.session.controller import Controller


# The top-level window, the simulator(s) will live inside of it
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(texts.APP_TITLE)

        # Size from the screen the window opens on, without panels and docks
        available = self.screen().availableGeometry()
        self.resize(int(available.width() * config.WINDOW_SCALE), int(available.height() * config.WINDOW_SCALE))

        # Set Rosen's tree into the view
        game = AbstractTree(presets.ROSEN_TREE)
        self.controller = Controller()
        self.controller.load(game, game.initial_state())

        self.tree_view = TreeView()
        self.setCentralWidget(self.tree_view)

        layout = self.controller.layout()
        if layout is not None:
            self.tree_view.show_layout(layout)

    # Show the window the way config.WINDOW_MODE says
    def show_by_config(self) -> None:
        if config.WINDOW_MODE == "fullscreen":
            self.showFullScreen()
        elif config.WINDOW_MODE == "maximized":
            self.showMaximized()
        else:
            self.show()