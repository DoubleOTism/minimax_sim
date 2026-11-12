"""
Side panel next to the tree.

At the top the input of the game (the tree text or the board),
below it the explanation of the current step and the counters.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from minimax_sim import texts
from minimax_sim.gui.help_button import help_button
from minimax_sim.session.controller import Algorithm
from minimax_sim.session.stats import Stats

# Space between the edge of the panel and its content in pixels
PANEL_PADDING = 4

# Rows of the counter table: label and the Stats field it shows
STATS_ROWS = (
    (texts.STATS_NODES, "nodes"),
    (texts.STATS_LEAVES, "leaves"),
    (texts.STATS_PRUNED, "pruned"),
    (texts.STATS_STEPS, "steps"),
)

# Lines the step explanation keeps room for
STEP_LINES = 4

# Whether the step explanation is open when the app starts
STEP_SHOWN_ON_START = True

# Limits of the panel width in pixels, between them the width follows the window
PANEL_MIN_WIDTH = 220
PANEL_MAX_WIDTH = 480


# Column of widgets on the right side of the page, scrolls when it does not fit
class SidePanel(QScrollArea):
    # source is the input of the game at the top, the counters sit at the bottom and the free height is between them
    def __init__(self, source: QWidget) -> None:
        super().__init__()
        self.setMinimumWidth(PANEL_MIN_WIDTH)
        self.setMaximumWidth(PANEL_MAX_WIDTH)
        self.setFrameShape(QFrame.Shape.NoFrame)

        # The content stretches to the panel size, scroll bars appear only when it cannot shrink more
        self.setWidgetResizable(True)
        content = QWidget()
        column = QVBoxLayout(content)
        column.setContentsMargins(PANEL_PADDING, PANEL_PADDING, PANEL_PADDING, PANEL_PADDING)
        self.setWidget(content)

        # The input never takes more height than it needs, the free height stays above the counters
        source.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        column.addWidget(source)

        # What happened in the current step, it folds away with the arrow, for example on a small projector
        # The question mark next to the arrow explains the symbols of the tree
        self.step_button = QToolButton()
        self.step_button.setText(texts.STEP_GROUP)
        self.step_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.step_button.setAutoRaise(True)
        self.step_button.setCheckable(True)
        self.step_button.toggled.connect(self._step_toggled)
        step_header = QHBoxLayout()
        step_header.addWidget(self.step_button)
        step_header.addStretch()
        step_header.addWidget(help_button(texts.SYMBOLS_LEGEND))
        column.addLayout(step_header)

        # The text sits in a frame like the groups, it keeps room for a few lines,
        # so the panel does not jump when the text gets longer
        self.step_frame = QFrame()
        self.step_frame.setFrameShape(QFrame.Shape.StyledPanel)
        step_column = QVBoxLayout(self.step_frame)
        self.step_label = QLabel()
        self.step_label.setWordWrap(True)
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.step_label.setMinimumHeight(self.step_label.fontMetrics().lineSpacing() * STEP_LINES)
        step_column.addWidget(self.step_label)
        column.addWidget(self.step_frame)
        self.step_button.setChecked(STEP_SHOWN_ON_START)
        self._step_toggled(STEP_SHOWN_ON_START)

        # Counters of both algorithms side by side, one row per Stats field
        # They stay at the bottom, folding the step explanation does not move them
        column.addStretch()
        stats_group = QGroupBox(texts.STATS_TITLE)
        table = QGridLayout(stats_group)
        column.addWidget(stats_group)
        self.algorithm_labels = {
            Algorithm.MINIMAX: QLabel(texts.ALGORITHM_MINIMAX),
            Algorithm.ALPHABETA: QLabel(texts.ALGORITHM_ALPHABETA),
        }
        self.stats_labels: dict[tuple[Algorithm, str], QLabel] = {}
        for col, algorithm in enumerate(Algorithm, start=1):
            table.addWidget(self.algorithm_labels[algorithm], 0, col, Qt.AlignmentFlag.AlignRight)
        for row, (text, field) in enumerate(STATS_ROWS, start=1):
            table.addWidget(QLabel(text), row, 0)
            for col, algorithm in enumerate(Algorithm, start=1):
                label = QLabel()
                table.addWidget(label, row, col, Qt.AlignmentFlag.AlignRight)
                self.stats_labels[(algorithm, field)] = label

    # Open or close the step explanation, the arrow points down while it is open
    def _step_toggled(self, shown: bool) -> None:
        self.step_frame.setVisible(shown)
        self.step_button.setArrowType(Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow)

    # Show the explanation of the current step
    def show_step(self, text: str) -> None:
        self.step_label.setText(text)

    # Fill the counter table, the column of the algorithm being stepped through is bold
    def show_stats(self, stats: dict[Algorithm, Stats | None], current: Algorithm) -> None:
        for algorithm, algorithm_stats in stats.items():
            bold = algorithm is current
            for _, field in STATS_ROWS:
                label = self.stats_labels[(algorithm, field)]
                value = getattr(algorithm_stats, field) if algorithm_stats is not None else texts.STATS_UNKNOWN
                label.setText(str(value))
                _set_bold(label, bold)
            _set_bold(self.algorithm_labels[algorithm], bold)


# Make the text of a label bold or normal
def _set_bold(label: QLabel, bold: bool) -> None:
    font = QFont(label.font())
    font.setBold(bold)
    label.setFont(font)
