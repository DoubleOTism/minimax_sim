"""
Main application window.

Each tab holds one simulator page, the toolbar and the status bar belong to the page that is shown.
"""

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSlider,
    QTabWidget,
    QToolBar,
    QWidget,
)

from minimax_sim import config, presets, texts
from minimax_sim.gui.board_source import BoardSource
from minimax_sim.gui.simulator_page import SimulatorPage
from minimax_sim.gui.tree_source import TreeSource
from minimax_sim.gui.tree_view import number_text
from minimax_sim.session.controller import Algorithm
from minimax_sim.session.snapshot import Status

# Playback speed in steps per second, the slider goes from 1 to MAX_SPEED
DEFAULT_SPEED = 3
MAX_SPEED = 10

# Width of the speed slider in pixels
SPEED_SLIDER_WIDTH = 120


# The top-level window with the simulator tabs
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(texts.APP_TITLE)

        # Size from the screen the window opens on, without panels and docks
        available = self.screen().availableGeometry()
        self.resize(int(available.width() * config.WINDOW_SCALE), int(available.height() * config.WINDOW_SCALE))

        # One simulator page per tab, the tab bar hides itself while there is only one
        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(True)
        self.setCentralWidget(self.tabs)
        loaded_presets = presets.load(config.PRESETS_FILE)
        tree_page = SimulatorPage(TreeSource(loaded_presets.trees))
        self._add_page(tree_page, texts.TAB_TREE)
        self._add_page(SimulatorPage(BoardSource(loaded_presets.boards)), texts.TAB_TICTACTOE)
        self.tabs.currentChanged.connect(self._page_changed)

        # F9 hides and shows the panel from anywhere in the window
        self._add_shortcut(Qt.Key.Key_F9, lambda: self._page().toggle_side_panel())

        # One toolbar at the bottom, split into three groups:
        # Algorithm settings on the left, stepping in the middle, view options on the right
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)

        # Algorithm choice, each item carries its Algorithm as data
        self.algorithm_box = QComboBox()
        self.algorithm_box.addItem(texts.ALGORITHM_MINIMAX, Algorithm.MINIMAX)
        self.algorithm_box.addItem(texts.ALGORITHM_ALPHABETA, Algorithm.ALPHABETA)
        self.algorithm_box.currentIndexChanged.connect(self._algorithm_selected)
        toolbar.addWidget(self.algorithm_box)

        # Pruning rule, each item carries the value of prune_on_equal as data
        self.prune_box = QComboBox()
        self.prune_box.addItem(texts.PRUNE_GE, True)
        self.prune_box.addItem(texts.PRUNE_GT, False)
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
        self._add_action(toolbar, texts.ZOOM_FIT, QKeySequence("Ctrl+0"), lambda: self._page().tree_view.fit_to_window())
        self._add_shortcut(QKeySequence(QKeySequence.StandardKey.ZoomIn), lambda: self._page().tree_view.zoom_in())
        self._add_shortcut(QKeySequence(QKeySequence.StandardKey.ZoomOut), lambda: self._page().tree_view.zoom_out())

        # Show only the nodes the search has reached so far, on every page
        self.hide_unvisited_box = QCheckBox(texts.HIDE_UNVISITED)
        self.hide_unvisited_box.toggled.connect(self._hide_unvisited_toggled)
        toolbar.addWidget(self.hide_unvisited_box)

        # Keep the active node in sight when the tree is zoomed in, on every page
        self.follow_box = QCheckBox(texts.FOLLOW_ACTIVE)
        self.follow_box.setChecked(tree_page.tree_view.follow_active)
        self.follow_box.toggled.connect(self._follow_toggled)
        toolbar.addWidget(self.follow_box)

        # Step number in the status bar at the bottom, after the last step also the result of the run
        self.step_label = QLabel()
        self.statusBar().addWidget(self.step_label)
        self.result_label = QLabel()
        self.statusBar().addWidget(self.result_label)

        self._page_changed()

    # Show the window the way config.WINDOW_MODE says
    def show_by_config(self) -> None:
        if config.WINDOW_MODE == "fullscreen":
            self.showFullScreen()
        elif config.WINDOW_MODE == "maximized":
            self.showMaximized()
        else:
            self.show()

    # Put a simulator page into a new tab
    def _add_page(self, page: SimulatorPage, title: str) -> None:
        page.loaded.connect(self._page_loaded)
        self.tabs.addTab(page, title)

    # The page in the tab that is shown
    def _page(self) -> SimulatorPage:
        return self.tabs.currentWidget()

    # Every page, for the view options that apply to all of them
    def _pages(self) -> list[SimulatorPage]:
        return [self.tabs.widget(i) for i in range(self.tabs.count())]

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

    # A page loaded a new game, a running playback would continue on a different run
    def _page_loaded(self) -> None:
        self._stop_playing()
        self._refresh()

    # Another tab was opened, the drop-downs show the settings of its page
    # The signals are blocked, so setting the drop-downs does not restart the run
    def _page_changed(self) -> None:
        self._stop_playing()
        controller = self._page().controller
        for box, value in ((self.algorithm_box, controller.algorithm), (self.prune_box, controller.prune_on_equal)):
            box.blockSignals(True)
            box.setCurrentIndex(box.findData(value))
            box.blockSignals(False)
        self._refresh()

    # Redraw the trees with or without the unvisited nodes
    def _hide_unvisited_toggled(self, hide: bool) -> None:
        for page in self._pages():
            page.tree_view.hide_unvisited = hide
        self._refresh()

    # Turn following the active node on or off
    def _follow_toggled(self, follow: bool) -> None:
        for page in self._pages():
            page.tree_view.follow_active = follow
        self._refresh()

    # Start or stop the playback, playing again after the last step starts from the beginning
    def _play_toggled(self, playing: bool) -> None:
        if playing:
            controller = self._page().controller
            if not controller.can_step_forward:
                controller.to_start()
                self._refresh()
            self.play_timer.start(self._step_interval())
            self.play_action.setText(texts.PAUSE)
        else:
            self.play_timer.stop()
            self.play_action.setText(texts.PLAY)

    # One step of the playback, it stops by itself after the last step
    def _play_step(self) -> None:
        controller = self._page().controller
        controller.step_forward()
        self._refresh()
        if not controller.can_step_forward:
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
        self._page().controller.set_algorithm(self.algorithm_box.currentData())
        self._refresh()

    # Start a new run with the pruning rule picked in the drop-down
    def _prune_rule_selected(self) -> None:
        self._stop_playing()
        self._page().controller.set_prune_on_equal(self.prune_box.currentData())
        self._refresh()

    def _to_start(self) -> None:
        self._stop_playing()
        self._page().controller.to_start()
        self._refresh()

    def _step_back(self) -> None:
        self._stop_playing()
        self._page().controller.step_back()
        self._refresh()

    def _step_forward(self) -> None:
        self._stop_playing()
        self._page().controller.step_forward()
        self._refresh()

    def _to_end(self) -> None:
        self._stop_playing()
        self._page().controller.to_end()
        self._refresh()

    # Bring the page, buttons and the step number in line with the controller of the shown page
    def _refresh(self) -> None:
        page = self._page()
        page.refresh()
        controller = page.controller

        can_back = controller.can_step_back
        can_forward = controller.can_step_forward
        self.to_start_action.setEnabled(can_back)
        self.step_back_action.setEnabled(can_back)
        self.step_forward_action.setEnabled(can_forward)
        self.to_end_action.setEnabled(can_forward)
        self.prune_box.setEnabled(controller.algorithm is Algorithm.ALPHABETA)

        # Position -1 is before the first event, shown as step 0
        current = controller.position + 1
        total = controller.total_steps
        if total is None:
            self.step_label.setText(texts.STEP_COUNTER_UNKNOWN_TOTAL.format(current=current))
        else:
            self.step_label.setText(texts.STEP_COUNTER.format(current=current, total=total))

        # The root is done only after the last step of a finished run
        root = controller.snapshot().nodes.get(())
        if root is not None and root.status is Status.DONE:
            self.result_label.setText(texts.RUN_FINISHED.format(value=number_text(root.value)))
        else:
            self.result_label.setText("")
