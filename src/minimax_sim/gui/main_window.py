"""
Main application window.
"""

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSlider,
    QToolBar,
    QToolButton,
    QWidget,
)

from minimax_sim import config, presets, texts
from minimax_sim.core.games.abstract_tree import AbstractTree, ParseError
from minimax_sim.gui.side_panel import SidePanel
from minimax_sim.gui.tree_view import TreeView, number_text
from minimax_sim.session.controller import Algorithm, Controller
from minimax_sim.session.snapshot import Status

# How the width is split between the tree and the side panel, 3 : 1
TREE_SHARE = 3
PANEL_SHARE = 1

# Width of the strip with the arrow that hides the panel, in pixels
ARROW_WIDTH = 14

# Playback speed in steps per second, the slider goes from 1 to MAX_SPEED
DEFAULT_SPEED = 3
MAX_SPEED = 10

# Width of the speed slider in pixels
SPEED_SLIDER_WIDTH = 120


# The top-level window, the simulator(s) will live inside of it
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(texts.APP_TITLE)

        # Size from the screen the window opens on, without panels and docks
        available = self.screen().availableGeometry()
        self.resize(int(available.width() * config.WINDOW_SCALE), int(available.height() * config.WINDOW_SCALE))

        self.controller = Controller()

        # Tree in the middle, side panel on the right, between them a thin button that hides the panel
        self.tree_view = TreeView()
        self.side_panel = SidePanel(presets.ROSEN_TREE)
        self.side_panel.load_requested.connect(self._load_tree)
        self.panel_button = QToolButton()
        self.panel_button.setArrowType(Qt.ArrowType.RightArrow)
        self.panel_button.setAutoRaise(True)
        self.panel_button.setToolTip(texts.PANEL_TOGGLE)
        self.panel_button.setFixedWidth(ARROW_WIDTH)
        self.panel_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.panel_button.clicked.connect(self._toggle_side_panel)

        central = QWidget()
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.tree_view, TREE_SHARE)
        row.addWidget(self.panel_button)
        row.addWidget(self.side_panel, PANEL_SHARE)
        self.setCentralWidget(central)

        # F9 hides and shows the panel from anywhere in the window
        self._add_shortcut(Qt.Key.Key_F9, self._toggle_side_panel)

        # One toolbar at the bottom, split into three groups:
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

        # Playback steps forward by itself, Space starts and stops it
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._play_step)
        self.play_action = QAction(texts.PLAY, self)
        self.play_action.setCheckable(True)
        self.play_action.setShortcut(QKeySequence(Qt.Key.Key_Space))
        self.play_action.toggled.connect(self._play_toggled)
        toolbar.addAction(self.play_action)

        # Speed of the playback in steps per second
        toolbar.addWidget(QLabel(texts.SPEED))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, MAX_SPEED)
        self.speed_slider.setValue(DEFAULT_SPEED)
        self.speed_slider.setFixedWidth(SPEED_SLIDER_WIDTH)
        self.speed_slider.valueChanged.connect(self._speed_changed)
        toolbar.addWidget(self.speed_slider)

        # Zoom of the tree, only fitting has a button
        # Zooming in and out is Ctrl + mouse wheel or Ctrl + plus and Ctrl + minus
        self._add_spacer(toolbar)
        self._add_action(toolbar, texts.ZOOM_FIT, QKeySequence("Ctrl+0"), self.tree_view.fit_to_window)
        self._add_shortcut(QKeySequence(QKeySequence.StandardKey.ZoomIn), self.tree_view.zoom_in)
        self._add_shortcut(QKeySequence(QKeySequence.StandardKey.ZoomOut), self.tree_view.zoom_out)

        # Show only the nodes the search has reached so far
        self.hide_unvisited_box = QCheckBox(texts.HIDE_UNVISITED)
        self.hide_unvisited_box.toggled.connect(self._hide_unvisited_toggled)
        toolbar.addWidget(self.hide_unvisited_box)

        # Keep the active node in sight when the tree is zoomed in
        self.follow_box = QCheckBox(texts.FOLLOW_ACTIVE)
        self.follow_box.setChecked(self.tree_view.follow_active)
        self.follow_box.toggled.connect(self._follow_toggled)
        toolbar.addWidget(self.follow_box)

        # Step number in the status bar at the bottom, after the last step also the result of the run
        self.step_label = QLabel()
        self.statusBar().addWidget(self.step_label)
        self.result_label = QLabel()
        self.statusBar().addWidget(self.result_label)

        self._load_tree(presets.ROSEN_TREE)

    # Show the window the way config.WINDOW_MODE says
    def show_by_config(self) -> None:
        if config.WINDOW_MODE == "fullscreen":
            self.showFullScreen()
        elif config.WINDOW_MODE == "maximized":
            self.showMaximized()
        else:
            self.show()

    # Button in the toolbar that calls slot when clicked or when the shortcut is pressed
    def _add_action(
        self, toolbar: QToolBar, text: str, shortcut: Qt.Key | QKeySequence, slot: Callable[[], None]
    ) -> QAction:
        action = QAction(text, self)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        toolbar.addAction(action)
        return action

    # Keyboard shortcut without a button, it works from anywhere in the window
    def _add_shortcut(self, shortcut: Qt.Key | QKeySequence, slot: Callable[[], None]) -> None:
        action = QAction(self)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        self.addAction(action)

    # Empty widget that takes all free space, so the items after it move to the right
    def _add_spacer(self, toolbar: QToolBar) -> None:
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

    # Parse the tree text and load it, or keep the old tree and show where the text is wrong
    def _load_tree(self, text: str) -> None:
        try:
            game = AbstractTree(text)
        except ParseError as error:
            self.side_panel.show_message(str(error), error.pos)
            return
        self._stop_playing()
        self.controller.load(game, game.initial_state())
        self.side_panel.show_message(self.controller.layout_error or "")
        self._refresh()

    # Hide or show the side panel, the arrow points to where the panel goes on the next click
    def _toggle_side_panel(self) -> None:
        show = self.side_panel.isHidden()
        self.side_panel.setVisible(show)
        self.panel_button.setArrowType(Qt.ArrowType.RightArrow if show else Qt.ArrowType.LeftArrow)

    # Redraw the tree with or without the unvisited nodes
    def _hide_unvisited_toggled(self, hide: bool) -> None:
        self.tree_view.hide_unvisited = hide
        self._refresh()

        # Turn following the active node on or off
    def _follow_toggled(self, follow: bool) -> None:
        self.tree_view.follow_active = follow
        self._refresh()

    # Start or stop the playback, playing again after the last step starts from the beginning
    def _play_toggled(self, playing: bool) -> None:
        if playing:
            if not self.controller.can_step_forward:
                self.controller.to_start()
                self._refresh()
            self.play_timer.start(self._step_interval())
            self.play_action.setText(texts.PAUSE)
        else:
            self.play_timer.stop()
            self.play_action.setText(texts.PLAY)

    # One step of the playback, it stops by itself after the last step
    def _play_step(self) -> None:
        self.controller.step_forward()
        self._refresh()
        if not self.controller.can_step_forward:
            self._stop_playing()

    # Any manual change stops the playback, so it does not run away from the lecturer
    def _stop_playing(self) -> None:
        self.play_action.setChecked(False)

    def _speed_changed(self) -> None:
        self.play_timer.setInterval(self._step_interval())

    # Milliseconds between two steps of the playback
    def _step_interval(self) -> int:
        return 1000 // self.speed_slider.value()

    # Start a new run with the algorithm picked in the drop-down
    def _algorithm_selected(self) -> None:
        self._stop_playing()
        self.controller.set_algorithm(self.algorithm_box.currentData())
        self._refresh()

    # Start a new run with the pruning rule picked in the drop-down
    def _prune_rule_selected(self) -> None:
        self._stop_playing()
        self.controller.set_prune_on_equal(self.prune_box.currentData())
        self._refresh()

    def _to_start(self) -> None:
        self._stop_playing()
        self.controller.to_start()
        self._refresh()

    def _step_back(self) -> None:
        self._stop_playing()
        self.controller.step_back()
        self._refresh()

    def _step_forward(self) -> None:
        self._stop_playing()
        self.controller.step_forward()
        self._refresh()

    def _to_end(self) -> None:
        self._stop_playing()
        self.controller.to_end()
        self._refresh()

    # Bring the tree, buttons and the step number in line with the controller
    def _refresh(self) -> None:
        snapshot = self.controller.snapshot()
        layout = self.controller.layout()
        if layout is None:
            self.tree_view.clear_tree()
        else:
            self.tree_view.draw(layout, snapshot, self.controller.algorithm is Algorithm.ALPHABETA)

        can_back = self.controller.can_step_back
        can_forward = self.controller.can_step_forward
        self.to_start_action.setEnabled(can_back)
        self.step_back_action.setEnabled(can_back)
        self.step_forward_action.setEnabled(can_forward)
        self.to_end_action.setEnabled(can_forward)
        self.prune_box.setEnabled(self.controller.algorithm is Algorithm.ALPHABETA)
        self.side_panel.show_stats(self.controller.stats(), self.controller.algorithm)

        # Position -1 is before the first event, shown as step 0
        current = self.controller.position + 1
        total = self.controller.total_steps
        if total is None:
            self.step_label.setText(texts.STEP_COUNTER_UNKNOWN_TOTAL.format(current=current))
        else:
            self.step_label.setText(texts.STEP_COUNTER.format(current=current, total=total))

        # The root is done only after the last step of a finished run
        root = snapshot.nodes.get(())
        if root is not None and root.status is Status.DONE:
            self.result_label.setText(texts.RUN_FINISHED.format(value=number_text(root.value)))
        else:
            self.result_label.setText("")
