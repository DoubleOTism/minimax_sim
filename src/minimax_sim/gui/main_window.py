"""
Main application window.
"""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QToolBar,
    QWidget,
)

from minimax_sim import config, presets, texts
from minimax_sim.core.games.abstract_tree import AbstractTree
from minimax_sim.gui.tree_view import TreeView
from minimax_sim.session.controller import Algorithm, Controller


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

        # One toolbar at the bottom, split into three groups
        # Algorithm settings on the left, stepping in the middle, view options on the right
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)

        # Algorithm choice, each item carries its Algorithm as data
        self.algorithm_box = QComboBox()
        self.algorithm_box.addItem(texts.ALGORITHM_MINIMAX, Algorithm.MINIMAX)
        self.algorithm_box.addItem(texts.ALGORITHM_ALPHABETA, Algorithm.ALPHABETA)
        self.algorithm_box.setCurrentIndex(self.algorithm_box.findData(self.controller.algorithm))
        self.algorithm_box.currentIndexChanged.connect(self._algorithm_selected)
        toolbar.addWidget(self.algorithm_box)

        # Pruning rule, each item carries the value of prune_on_equal as data
        self.prune_box = QComboBox()
        self.prune_box.addItem(texts.PRUNE_GE, True)
        self.prune_box.addItem(texts.PRUNE_GT, False)
        self.prune_box.setCurrentIndex(self.prune_box.findData(self.controller.prune_on_equal))
        self.prune_box.currentIndexChanged.connect(self._prune_rule_selected)
        toolbar.addWidget(self.prune_box)

        # Stepping buttons, each with its keyboard shortcut
        self._add_spacer(toolbar)
        self.to_start_action = self._add_action(toolbar, texts.STEP_TO_START, Qt.Key.Key_Home, self._to_start)
        self.step_back_action = self._add_action(toolbar, texts.STEP_BACK, Qt.Key.Key_Left, self._step_back)
        self.step_forward_action = self._add_action(toolbar, texts.STEP_FORWARD, Qt.Key.Key_Right, self._step_forward)
        self.to_end_action = self._add_action(toolbar, texts.STEP_TO_END, Qt.Key.Key_End, self._to_end)

        # Show only the nodes the search has reached so far
        self._add_spacer(toolbar)
        self.hide_unvisited_box = QCheckBox(texts.HIDE_UNVISITED)
        self.hide_unvisited_box.toggled.connect(self._hide_unvisited_toggled)
        toolbar.addWidget(self.hide_unvisited_box)

        # Step number in the status bar at the bottom
        self.step_label = QLabel()
        self.statusBar().addWidget(self.step_label)

        self._refresh()

    # Show the window the way config.WINDOW_MODE says
    def show_by_config(self) -> None:
        if config.WINDOW_MODE == "fullscreen":
            self.showFullScreen()
        elif config.WINDOW_MODE == "maximized":
            self.showMaximized()
        else:
            self.show()

    # Button in the toolbar that calls slot when clicked or when key is pressed
    def _add_action(self, toolbar: QToolBar, text: str, key: Qt.Key, slot: Callable[[], None]) -> QAction:
        action = QAction(text, self)
        action.setShortcut(QKeySequence(key))
        action.triggered.connect(slot)
        toolbar.addAction(action)
        return action

    # Empty widget that takes all free space, so the items after it move to the right
    def _add_spacer(self, toolbar: QToolBar) -> None:
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

    # Redraw the tree with or without the unvisited nodes
    def _hide_unvisited_toggled(self, hide: bool) -> None:
        self.tree_view.hide_unvisited = hide
        self._refresh()

    # Start a new run with the algorithm picked in the drop-down
    def _algorithm_selected(self) -> None:
        self.controller.set_algorithm(self.algorithm_box.currentData())
        self._refresh()

    # Start a new run with the pruning rule picked in the drop-down
    def _prune_rule_selected(self) -> None:
        self.controller.set_prune_on_equal(self.prune_box.currentData())
        self._refresh()

    def _to_start(self) -> None:
        self.controller.to_start()
        self._refresh()

    def _step_back(self) -> None:
        self.controller.step_back()
        self._refresh()

    def _step_forward(self) -> None:
        self.controller.step_forward()
        self._refresh()

    def _to_end(self) -> None:
        self.controller.to_end()
        self._refresh()

    # Bring the tree, buttons and the step number in line with the controller
    def _refresh(self) -> None:
        layout = self.controller.layout()
        if layout is not None:
            self.tree_view.draw(layout, self.controller.snapshot())

        can_back = self.controller.can_step_back
        can_forward = self.controller.can_step_forward
        self.to_start_action.setEnabled(can_back)
        self.step_back_action.setEnabled(can_back)
        self.step_forward_action.setEnabled(can_forward)
        self.to_end_action.setEnabled(can_forward)
        self.prune_box.setEnabled(self.controller.algorithm is Algorithm.ALPHABETA)

        # Position -1 is before the first event, shown as step 0
        current = self.controller.position + 1
        total = self.controller.total_steps
        if total is None:
            self.step_label.setText(texts.STEP_COUNTER_UNKNOWN_TOTAL.format(current=current))
        else:
            self.step_label.setText(texts.STEP_COUNTER.format(current=current, total=total))