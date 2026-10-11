"""
Side panel next to the tree.

For now it holds the text of the tree, the counters and the step explanation will come here too.
It only shows things and asks for actions, the main window decides what happens.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

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


# Column of widgets on the right side of the window, scrolls when it does not fit
class SidePanel(QScrollArea):
    # Sent with the tree text when the button or Ctrl+Enter asks to load it
    load_requested = Signal(str)

    def __init__(self, tree_text: str) -> None:
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

        # Tree text, long lines scroll sideways instead of wrapping
        # Enter makes a new line, so loading has its own shortcut
        column.addWidget(QLabel(texts.TREE_LABEL))
        self.tree_edit = QPlainTextEdit(tree_text)
        self.tree_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        column.addWidget(self.tree_edit, 1)
        for keys in ("Ctrl+Return", "Ctrl+Enter"):
            shortcut = QShortcut(QKeySequence(keys), self.tree_edit)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(self._request_load)

        load_button = QPushButton(texts.TREE_LOAD)
        load_button.clicked.connect(self._request_load)
        column.addWidget(load_button)

        # Problems with the tree, empty when all is fine
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        column.addWidget(self.message_label)

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

    # Show a problem with the tree, with pos the cursor jumps to where the text is wrong
    def show_message(self, message: str, pos: int | None = None) -> None:
        self.message_label.setText(message)
        if pos is not None:
            cursor = self.tree_edit.textCursor()
            cursor.setPosition(pos)
            self.tree_edit.setTextCursor(cursor)
            self.tree_edit.setFocus()

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

    def _request_load(self) -> None:
        self.load_requested.emit(self.tree_edit.toPlainText())


# Make the text of a label bold or normal
def _set_bold(label: QLabel, bold: bool) -> None:
    font = QFont(label.font())
    font.setBold(bold)
    label.setFont(font)
