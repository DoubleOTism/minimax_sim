"""
One simulator: the search tree, and next to it the side panel with the game input and the counters.

The main window has one page per tab, its toolbar controls the page that is shown.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QToolButton, QWidget

from minimax_sim import texts
from minimax_sim.core.game import Game
from minimax_sim.gui.side_panel import SidePanel
from minimax_sim.gui.tree_view import TreeView
from minimax_sim.session.controller import Algorithm, Controller

# How the width is split between the tree and the side panel, 3 : 1
TREE_SHARE = 3
PANEL_SHARE = 1

# Width of the strip with the arrow that hides the panel, in pixels
ARROW_WIDTH = 14


# Tree, side panel and the controller of their search run
# source is the game input, a widget with the game_requested signal,
# request_load() that sends the first game and show_message() for problems
class SimulatorPage(QWidget):
    # Sent after a new game was loaded, the window then refreshes the toolbar and the status bar
    loaded = Signal()

    def __init__(self, source: QWidget) -> None:
        super().__init__()
        self.controller = Controller()
        self.source = source
        source.game_requested.connect(self._load)

        # Tree in the middle, side panel on the right, between them a thin button that hides the panel
        self.tree_view = TreeView()
        self.side_panel = SidePanel(source)
        self.panel_button = QToolButton()
        self.panel_button.setArrowType(Qt.ArrowType.RightArrow)
        self.panel_button.setAutoRaise(True)
        self.panel_button.setToolTip(texts.PANEL_TOGGLE)
        self.panel_button.setFixedWidth(ARROW_WIDTH)
        self.panel_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.panel_button.clicked.connect(self.toggle_side_panel)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.tree_view, TREE_SHARE)
        row.addWidget(self.panel_button)
        row.addWidget(self.side_panel, PANEL_SHARE)

        source.request_load()

    # Hide or show the side panel, the arrow points to where the panel goes on the next click
    def toggle_side_panel(self) -> None:
        show = self.side_panel.isHidden()
        self.side_panel.setVisible(show)
        self.panel_button.setArrowType(Qt.ArrowType.RightArrow if show else Qt.ArrowType.LeftArrow)

    # Draw the tree and the counters for the current step
    def refresh(self) -> None:
        layout = self.controller.layout()
        if layout is None:
            self.tree_view.clear_tree()
        else:
            show_bounds = self.controller.algorithm is Algorithm.ALPHABETA
            self.tree_view.draw(layout, self.controller.snapshot(), show_bounds)
        self.side_panel.show_stats(self.controller.stats(), self.controller.algorithm)

    # Start a new run over the game, a tree too big to draw is reported in the source
    def _load(self, game: Game, depth_limit: int | None) -> None:
        self.controller.load(game, game.initial_state(), depth_limit)
        self.source.show_message(self.controller.layout_error or "")
        self.loaded.emit()
