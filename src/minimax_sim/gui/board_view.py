"""
Tic-tac-toe board that is only shown, not clicked.

The panel shows the position in a node of the search tree with it,
the bubble over a node gets the same board as HTML.
The cell of the last move is highlighted.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QApplication, QWidget

from minimax_sim.core.games.tictactoe import EMPTY_BOARD, Board

# Width of the lines between the cells in pixels
GRID_LINE_WIDTH = 2

# Width of one cell and size of the marks in the bubble over a node, in pixels
HTML_CELL_SIZE = 24
HTML_MARK_SIZE = 16


# Read-only 3x3 board drawn by hand, cell_size is the side of one cell in pixels
class BoardView(QWidget):
    def __init__(self, cell_size: int) -> None:
        super().__init__()
        self.cell_size = cell_size
        self.setFixedSize(3 * cell_size, 3 * cell_size)
        self._board = EMPTY_BOARD
        self._last_move: int | None = None

    # Show another position, last_move is the cell to highlight, None highlights nothing
    def show_board(self, board: Board, last_move: int | None) -> None:
        self._board = board
        self._last_move = last_move
        self.update()

    # Called by Qt whenever the widget needs to be drawn
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        size = self.cell_size

        # Large bold marks, half the height of a cell
        font = QFont()
        font.setPixelSize(size // 2)
        font.setBold(True)
        painter.setFont(font)

        # Cells first, the cell of the last move gets the highlight colour
        for cell, mark in enumerate(self._board):
            rect = QRectF((cell % 3) * size, (cell // 3) * size, size, size)
            highlighted = cell == self._last_move
            painter.fillRect(rect, palette.highlight() if highlighted else palette.base())
            painter.setPen(palette.highlightedText().color() if highlighted else palette.text().color())
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, mark)

        # Lines of the board over the cells, the outer frame included
        painter.setPen(QPen(palette.mid().color(), GRID_LINE_WIDTH))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        half = GRID_LINE_WIDTH / 2
        painter.drawRect(QRectF(half, half, 3 * size - GRID_LINE_WIDTH, 3 * size - GRID_LINE_WIDTH))
        for line in (1, 2):
            painter.drawLine(line * size, 0, line * size, 3 * size)
            painter.drawLine(0, line * size, 3 * size, line * size)


# The same board as an HTML table, for the bubble over a node
def board_html(board: Board, last_move: int | None) -> str:
    palette = QApplication.palette()
    highlight = palette.highlight().color().name()
    highlighted_text = palette.highlightedText().color().name()
    size = f'width="{HTML_CELL_SIZE}" align="center"'
    rows = []
    for row in range(3):
        cells = []
        for cell in range(row * 3, row * 3 + 3):
            mark = board[cell] or "&nbsp;"
            if cell == last_move:
                cells.append(f'<td {size} bgcolor="{highlight}" style="color: {highlighted_text}">{mark}</td>')
            else:
                cells.append(f"<td {size}>{mark}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    table_style = f"border-collapse: collapse; font-size: {HTML_MARK_SIZE}px; font-weight: bold"
    return f'<table border="1" cellspacing="0" cellpadding="2" style="{table_style}">' + "".join(rows) + "</table>"
