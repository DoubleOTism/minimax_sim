"""
Input of tic-tac-toe, shown at the top of the side panel.

A preset fills the board, the depth limit and the scoring at once.

The starting position can also be clicked on a 3x3 board.
Each click changes the cell from empty to X, from X to O and from O back to empty.

Who moves follows from the marks, X always starts.

Below the input the panel shows the position in the current node of the tree
and what the numbers in the nodes mean.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from minimax_sim import texts
from minimax_sim.core.games.tictactoe import Board, TicTacToe, board_from_text, winner
from minimax_sim.core.search import is_leaf
from minimax_sim.gui.board_view import BoardItem, BoardView, board_html
from minimax_sim.gui.help_button import help_button
from minimax_sim.presets import BoardPreset

# Side of one cell of the clickable board in pixels
CELL_SIZE = 64

# Side of one cell of the board that shows the node, in pixels
NODE_CELL_SIZE = 36

# Mark that follows after a click on a cell
NEXT_MARK = {"": "X", "X": "O", "O": ""}

# Highest depth limit, a game of tic-tac-toe never has more moves
MAX_DEPTH_LIMIT = 9


# Presets, clickable board, depth limit and scoring, sends a game when a valid position should be loaded
class BoardSource(QWidget):
    # Sent with the game and its depth limit, None means no limit
    game_requested = Signal(object, object)

    # presets fill the drop-down, the first one is set up on start
    def __init__(self, presets: list[BoardPreset]) -> None:
        super().__init__()
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)

        # Starting position: preset, hint, the board in the middle and the clear button under it
        start_group = QGroupBox(texts.BOARD_GROUP)
        start_column = QVBoxLayout(start_group)

        # Prepared positions, choosing one sets everything up and loads it
        # A loaded position that matches no preset shows as the custom position
        self.preset_box = QComboBox()
        self.preset_box.setPlaceholderText(texts.PRESET_CUSTOM_POSITION)
        for preset in presets:
            self.preset_box.addItem(preset.name, preset)
        self.preset_box.activated.connect(self._preset_chosen)
        preset_form = QFormLayout()
        preset_form.addRow(texts.PRESET_LABEL, self.preset_box)
        start_column.addLayout(preset_form)
        start_column.addWidget(QLabel(texts.BOARD_HINT), 0, Qt.AlignmentFlag.AlignHCenter)

        # Board of 9 buttons, row by row like the cells of the game
        # Buttons sit close together, the thin gap between them draws the lines of the board
        grid = QGridLayout()
        grid.setSpacing(2)

        # Large bold marks, half the height of a cell
        font = QFont()
        font.setPixelSize(CELL_SIZE // 2)
        font.setBold(True)

        # Every button gets its cell number, so a click knows which cell it was
        # cell // 3 is the row and cell % 3 the column
        # The lambda keeps cell as a default argument, otherwise every button would get the last one
        self.cells: list[QPushButton] = []
        for cell in range(9):
            button = QPushButton()
            button.setFixedSize(CELL_SIZE, CELL_SIZE)
            button.setFont(font)
            button.clicked.connect(lambda _, cell=cell: self._cell_clicked(cell))
            grid.addWidget(button, cell // 3, cell % 3)
            self.cells.append(button)
        start_column.addLayout(_centered(grid))

        clear_button = QPushButton(texts.BOARD_CLEAR)
        clear_button.clicked.connect(self._clear)
        start_column.addWidget(clear_button, 0, Qt.AlignmentFlag.AlignHCenter)
        column.addWidget(start_group)

        # Search settings and the load button, the fields keep their natural width
        search_group = QGroupBox(texts.SEARCH_GROUP)
        search_column = QVBoxLayout(search_group)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        # Depth limit, 0 means no limit and shows as text
        self.depth_box = QSpinBox()
        self.depth_box.setRange(0, MAX_DEPTH_LIMIT)
        self.depth_box.setSpecialValueText(texts.DEPTH_LIMIT_NONE)
        form.addRow(texts.DEPTH_LIMIT_LABEL, self.depth_box)
        search_column.addLayout(form)

        # A faster win is worth more, see TicTacToe
        # The question mark next to it explains what it changes
        self.prefer_fast_box = QCheckBox(texts.PREFER_FAST)
        self.prefer_fast_box.setToolTip(texts.PREFER_FAST_TIP)
        prefer_fast_row = QHBoxLayout()
        prefer_fast_row.addWidget(self.prefer_fast_box)
        prefer_fast_row.addWidget(help_button(texts.PREFER_FAST_TIP))
        prefer_fast_row.addStretch()
        search_column.addLayout(prefer_fast_row)

        load_button = QPushButton(texts.BOARD_LOAD)
        load_button.clicked.connect(self.request_load)
        search_column.addWidget(load_button)

        # Problems with the position, empty when all is fine
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        search_column.addWidget(self.message_label)
        column.addWidget(search_group)

        # Position in the node the tree shows, next to it the last move and what happens there
        # The question mark in the corner explains what the numbers in the nodes mean,
        # its text follows the scoring of the loaded game and is set on every load
        node_group = QGroupBox(texts.NODE_GROUP)
        node_row = QHBoxLayout(node_group)
        self.node_board = BoardView(NODE_CELL_SIZE)
        node_row.addWidget(self.node_board)
        self.node_label = QLabel()
        self.node_label.setWordWrap(True)
        node_row.addWidget(self.node_label, 1)
        self.legend_help = help_button("")
        node_row.addWidget(self.legend_help, 0, Qt.AlignmentFlag.AlignTop)
        column.addWidget(node_group)

        # Game and depth limit that were sent last, the node texts are worked out from them
        self._game: TicTacToe | None = None
        self._depth_limit: int | None = None

        # The page loads the first preset right after this
        self._set_up(presets[0])

    # Load the position on the board with the chosen depth limit and scoring
    def request_load(self) -> None:
        board = tuple(button.text() for button in self.cells)
        try:
            game = TicTacToe(board, prefer_fast=self.prefer_fast_box.isChecked())
        except ValueError as error:
            self.show_message(str(error))
            return
        self._game = game
        self._depth_limit = self.depth_box.value() or None
        self.preset_box.setCurrentIndex(self._matching_preset(board, self._depth_limit, game.prefer_fast))
        wins = texts.LEGEND_WINS_FAST if game.prefer_fast else texts.LEGEND_WINS_PLAIN
        self.legend_help.setToolTip(texts.LEGEND.format(wins=wins))
        self.game_requested.emit(game, self._depth_limit)

    # Show a message under the load button, empty clears it
    def show_message(self, message: str) -> None:
        self.message_label.setText(message)

    # Show the position in a node of the tree
    #   move   cell of the move that led to the node, None in the root
    #   depth  number of moves from the root
    def show_node(self, state: Board, move: int | None, depth: int) -> None:
        self.node_board.show_board(state, move)
        self.node_label.setText(self._node_text(state, move, depth))

    # Board drawn in the tree in place of an expanded node
    def node_picture(self, state: Board, move: int | None, depth: int) -> BoardItem:
        return BoardItem(state, move)

    # Text of the bubble over a node, the board and the same lines as in the panel
    def node_tooltip(self, state: Board, move: int | None, depth: int) -> str:
        return board_html(state, move) + self._node_text(state, move, depth).replace("\n", "<br>")

    # Last move and what happens in the node: who moves, who won, or the estimate at the depth limit
    def _node_text(self, state: Board, move: int | None, depth: int) -> str:
        game = self._game
        lines = []
        if move is not None:
            lines.append(texts.NODE_LAST_MOVE.format(mark=state[move], cell=game.move_label(move)))
        mark = winner(state)
        if mark is not None:
            lines.append(texts.NODE_WIN.format(mark=mark, value=game.utility(state, depth)))
        elif game.is_terminal(state):
            lines.append(texts.NODE_DRAW)
        elif is_leaf(game, state, depth, self._depth_limit):
            lines.append(texts.NODE_ESTIMATE.format(value=game.evaluate(state)))
        elif game.is_max_turn(state):
            lines.append(texts.NODE_X_MOVES)
        else:
            lines.append(texts.NODE_O_MOVES)
        return "\n".join(lines)

    # Set up the board and the settings of the chosen preset and load it
    def _preset_chosen(self) -> None:
        self._set_up(self.preset_box.currentData())
        self.request_load()

    # Put a preset on the board and into the settings, without loading it
    def _set_up(self, preset: BoardPreset) -> None:
        for button, mark in zip(self.cells, board_from_text(preset.board), strict=True):
            button.setText(mark)
        self.depth_box.setValue(preset.depth_limit or 0)
        self.prefer_fast_box.setChecked(preset.prefer_fast)

    # Index of the preset with this position and these settings, -1 shows the custom position
    def _matching_preset(self, board: Board, depth_limit: int | None, prefer_fast: bool) -> int:
        wanted = (board, depth_limit, prefer_fast)
        for index in range(self.preset_box.count()):
            preset = self.preset_box.itemData(index)
            if (board_from_text(preset.board), preset.depth_limit, preset.prefer_fast) == wanted:
                return index
        return -1

    # Next mark in the clicked cell
    def _cell_clicked(self, cell: int) -> None:
        button = self.cells[cell]
        button.setText(NEXT_MARK[button.text()])

    # Empty every cell
    def _clear(self) -> None:
        for button in self.cells:
            button.setText("")


# Layout in a row with free space on both sides, so it stays in the middle
def _centered(layout: QLayout) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addStretch()
    row.addLayout(layout)
    row.addStretch()
    return row
