"""
Side panel next to the tree.

At the top the input of the game (the tree text or the board), below it the counters.
The step explanation will come here too.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from minimax_sim import texts
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

# Limits of the panel width in pixels, between them the width follows the window
PANEL_MIN_WIDTH = 220
PANEL_MAX_WIDTH = 480


# Column of widgets on the right side of the page, scrolls when it does not fit
class SidePanel(QScrollArea):
    # source is the input of the game, it takes all the free height
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

        column.addWidget(source, 1)

        # Counters of both algorithms side by side, one row per Stats field
        column.addWidget(QLabel(texts.STATS_TITLE))
        table = QGridLayout()
        column.addLayout(table)
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