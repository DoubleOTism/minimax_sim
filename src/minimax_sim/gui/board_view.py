"""
Tic-tac-toe board that is only shown, not clicked.

The panel shows the position in a node of the search tree with it,
the bubble over a node gets the same board as HTML
and an expanded node of the tree is drawn as the board itself.
The cell of the last move is highlighted.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import QApplication, QGraphicsItem, QStyleOptionGraphicsItem, QWidget

from minimax_sim.core.games.tictactoe import EMPTY_BOARD, Board

# Width of the lines between the cells in pixels
GRID_LINE_WIDTH = 2

# Width of one cell and size of the marks in the bubble over a node, in pixels
HTML_CELL_SIZE = 24
HTML_MARK_SIZE = 16

# Width of one cell of the board in the tree, the tree scales the board to the size of its nodes
ITEM_CELL_SIZE = 30


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
        paint_board(painter, self.palette(), self._board, self._last_move, self.cell_size)


# The same board as an item of the search tree, drawn in place of an expanded node
class BoardItem(QGraphicsItem):
    def __init__(self, board: Board, last_move: int | None) -> None:
        super().__init__()
        self._board = board
        self._last_move = last_move

    # Called by Qt for the area the item draws in, the whole board
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, 3 * ITEM_CELL_SIZE, 3 * ITEM_CELL_SIZE)

    # Called by Qt whenever the item needs to be drawn, widget is None when the scene is rendered into an image
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        palette = widget.palette() if widget is not None else QApplication.palette()
        paint_board(painter, palette, self._board, self._last_move, ITEM_CELL_SIZE)


# Draw a board with its top left corner at 0, 0, size is the side of one cell
# last_move is the cell to highlight, None highlights nothing
def paint_board(painter: QPainter, palette: QPalette, board: Board, last_move: int | None, size: int) -> None:
    # Large bold marks, half the height of a cell
    font = QFont()
    font.setPixelSize(size // 2)
    font.setBold(True)
    painter.setFont(font)

    # Cells first, the cell of the last move gets the highlight colour
    for cell, mark in enumerate(board):
        rect = QRectF((cell % 3) * size, (cell // 3) * size, size, size)
        highlighted = cell == last_move
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
