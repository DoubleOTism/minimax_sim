"""
Tic-tac-toe on a 3x3 board.

The board is a tuple of 9 cells, row by row from the top left corner:

    0 1 2
    3 4 5
    6 7 8

A cell holds "X", "O" or "" when it is empty.
X always starts and is MAX, O is MIN. Who is on the move follows from the board,
so a position where O moves is the same game seen from the other player.
A move is the index of the empty cell to play.
"""

from collections.abc import Sequence

from minimax_sim import texts

# Game state, the 9 cells row by row
type Board = tuple[str, ...]

# Board without any mark
EMPTY_BOARD: Board = ("",) * 9

# Rows, columns and both diagonals
LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Value of a win, always higher than any value of the heuristic
WIN_VALUE = 10


# Board from text, 9 characters row by row, "." is an empty cell, spaces are ignored
#   board_from_text("X.. .O. ..X")
def board_from_text(text: str) -> Board:
    return tuple("" if char == "." else char for char in text.replace(" ", ""))


# Every mark that fills a whole line, two of them only in an impossible position
def _winners(board: Board) -> set[str]:
    return {board[a] for a, b, c in LINES if board[a] and board[a] == board[b] == board[c]}


# Mark that fills a whole line, None if nobody has won
def winner(board: Board) -> str | None:
    marks = _winners(board)
    return marks.pop() if marks else None


# Rules of tic-tac-toe, the search can start from any valid position
#   prefer_fast  a faster win is worth more, each empty cell left adds 1 to WIN_VALUE
class TicTacToe:
    # The starting position must be reachable in a real game
    def __init__(self, board: Sequence[str] = EMPTY_BOARD, prefer_fast: bool = True) -> None:
        board = tuple(board)
        x_count, o_count = board.count("X"), board.count("O")
        if len(board) != 9 or x_count + o_count + board.count("") != 9:
            raise ValueError(texts.TTT_BAD_BOARD)
        if x_count - o_count not in (0, 1):
            raise ValueError(texts.TTT_BAD_COUNTS.format(x=x_count, o=o_count))

        # The game ends with the winning move, the winner made the last one
        winners = _winners(board)
        if len(winners) == 2:
            raise ValueError(texts.TTT_TWO_WINNERS)
        if (winners == {"X"} and x_count == o_count) or (winners == {"O"} and x_count > o_count):
            raise ValueError(texts.TTT_MOVE_AFTER_WIN)
        self.board = board
        self.prefer_fast = prefer_fast

    # The position the game was created with
    def initial_state(self) -> Board:
        return self.board

    # X moves when both players have the same number of marks
    def is_max_turn(self, state: Board) -> bool:
        return state.count("X") == state.count("O")

    # Empty cells from the top left corner
    def moves(self, state: Board) -> list[int]:
        return [cell for cell in range(9) if not state[cell]]

    # Board with the mark of the player on the move in the chosen cell
    def apply(self, state: Board, move: int) -> Board:
        mark = "X" if self.is_max_turn(state) else "O"
        return state[:move] + (mark,) + state[move + 1 :]

    # Somebody has won or the board is full
    def is_terminal(self, state: Board) -> bool:
        return winner(state) is not None or all(state)

    # Win for X is positive, win for O negative, draw 0, depth does not matter here
    def utility(self, state: Board, depth: int) -> float:
        mark = winner(state)
        if mark is None:
            return 0
        value = WIN_VALUE + (state.count("") if self.prefer_fast else 0)
        return value if mark == "X" else -value

    # Lines X can still fill minus lines O can still fill, between -8 and 8
    def evaluate(self, state: Board) -> float:
        open_for_x = sum(all(state[cell] != "O" for cell in line) for line in LINES)
        open_for_o = sum(all(state[cell] != "X" for cell in line) for line in LINES)
        return open_for_x - open_for_o

    # Cell name, columns a to c from the left, rows 1 to 3 from the top
    def move_label(self, move: int) -> str:
        return "abc"[move % 3] + str(move // 3 + 1)
