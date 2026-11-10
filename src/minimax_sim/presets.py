"""
Trees and tic-tac-toe positions offered in the side panel as presets.

More can be added in a JSON file given by MINIMAX_PRESETS, they come after the built-in ones.
Both parts are optional:

    {
        "trees": {
            "Example from the seminar": "((3 5) (2 9))"
        },
        "tictactoe": {
            "Corners against the centre": {"board": "X.. .O. ..X", "depth_limit": null, "prefer_fast": true}
        }
    }

In a position only board is required, depth_limit null means no limit and prefer_fast is true when left out.
"""

import json
from dataclasses import dataclass

from minimax_sim import texts
from minimax_sim.core.games.tictactoe import TicTacToe, board_from_text

# Rosen's example tree from the lecture materials
ROSEN_TREE = "( (((3 17) (2 12)) ((15) (25 0))) (((2 5) (3)) ((2 14))) )"

# Best moves always come first, alpha-beta evaluates only 7 of the 16 leaves
BEST_ORDER_TREE = "((((14 25) (13 28)) ((16 17) (2 9))) (((5 7) (3 19)) ((12 22) (10 29))))"

# The same leaves with the best moves last, alpha-beta prunes nothing
WORST_ORDER_TREE = "((((29 10) (22 12)) ((19 3) (7 5))) (((9 2) (17 16)) ((28 13) (25 14))))"

# Depth 7 with negative and decimal values, 569 nodes, for the counters and zooming
LARGE_TREE = """\
(
  (
    (
      (
        (((19 16) (11 17 -20)) ((6.3 11) (5 2 12) (-3.2 -2 -11)) ((-1 4.2 7) (17 -13) (18 5)))
        (((10 -19) (-12 13 -14)) ((-11 -6 -13) (10 14 5) (15 12 5)) ((-3 -7.0) (13 3 -4)))
        (((11 15) (-2 -14 12)) ((-9 10) (11 -8)) ((8.3 -1.0) (-15 -8 19) (-3 20)))
      )
      (
        (((16 11) (-12 10 18)) ((6 -12 17) (4 13) (-14 -16)))
        (((-19 -0.5 8) (11 16)) ((13 19) (-6 -16) (-8 -9 0.9)))
      )
      (
        (((-19 0.6) (-12 -9 7) (-15 -9 -4)) ((6 -9) (8 5.9)))
        (((-15 1) (-9 2)) ((16 -7) (-3 16)))
      )
    )
    (
      (
        (((15 5.6 -1.3) (2 -9)) ((-3.7 -16 0) (-16 7.3) (-20 -5.3)) ((1.2 2) (18 19)))
        (((18 -13) (12 -4 2)) ((-19 1 -13) (0 -19)))
      )
      (
        (((9.9 -13 -7.5) (-1 1.6)) ((-5 -6) (-19 14)))
        (((-11 -19) (6 0) (17 -6.4)) ((12 1 0) (-20 -5)) ((12 5) (-6 -3 -8)))
        (((15 17) (20 11)) ((13 -18) (-1 -4 4.8)))
      )
      (
        (((16 -2.1 13) (12 -7.2 15)) ((1.9 -10) (-2 4)) ((18 7 14) (-19 14)))
        (((12 -20) (-3.9 18)) ((9.7 -16) (-1 2) (-13 -5)))
      )
    )
  )
  (
    (
      (
        (((9.5 -1) (-6 7)) ((11 -9 9) (2 2) (17 -11)) ((-12 1 0) (8 14)))
        (((-11 -13) (9 5)) ((6 11 20) (13 2 -17)) ((-3 -4 1.6) (10 10 -18)))
      )
      (
        (((-3 -7 12) (3 3.8)) ((-11 -6) (-10 -15) (13 15 -9.4)) ((12 10) (1 18 11)))
        (((-12 6.2) (9 -3)) ((-7 6 12) (-1 19 0.2) (11 1 -16)))
      )
      (
        (((4 18 -19) (7 13)) ((-3 11 3.6) (5 14)))
        (((-11 -12 16) (-18 -1)) ((14 -12) (-17 -11)))
        (((14 -1 3) (3.6 0 0.2) (-8.1 -4)) ((-8 -15) (-8 -10)))
      )
    )
    (
      (
        (((14 7) (3 -1 8)) ((-7 -13 2) (-10 -5.9 7) (-11 20)) ((5 0.4) (11 -14)))
        (((9 20) (4.0 -4 -15) (14 13)) ((-2 1.8) (8 4) (9 14 8.0)))
      )
      (
        (((0.7 -18) (18 1 -1)) ((9 5) (0 11)))
        (((-13 17) (-19 -7) (13 -12)) ((0 7) (2 13 13)))
      )
    )
  )
)
"""

# Name and tree text of every built-in preset, the first one is loaded on start
BUILT_IN = (
    (texts.PRESET_ROSEN, ROSEN_TREE),
    (texts.PRESET_BEST_ORDER, BEST_ORDER_TREE),
    (texts.PRESET_WORST_ORDER, WORST_ORDER_TREE),
    (texts.PRESET_LARGE, LARGE_TREE),
)


# Tic-tac-toe position with the settings it is loaded with
#   board        9 cells row by row, "." is an empty cell, spaces are ignored
#   depth_limit  None means no limit
#   prefer_fast  a faster win is worth more, see TicTacToe
@dataclass(frozen=True, slots=True)
class BoardPreset:
    name: str
    board: str
    depth_limit: int | None
    prefer_fast: bool = True


# Built-in tic-tac-toe presets, the first one is loaded on start
# Every one of them can be drawn, the largest has 1061 nodes
TICTACTOE_BUILT_IN = (
    # 82 nodes, alpha-beta visits 36, estimates in all leaves
    BoardPreset(texts.TTT_PRESET_EMPTY_2, "... ... ...", 2),
    # 586 nodes, alpha-beta visits 163, a wide tree that shows the saving best
    BoardPreset(texts.TTT_PRESET_EMPTY_3, "... ... ...", 3),
    # O moves, the whole game to the end, a draw
    BoardPreset(texts.TTT_PRESET_DRAW, "X.. .O. ..X", None),
    # O moves after taking an edge, X forces a win with a fork
    BoardPreset(texts.TTT_PRESET_FORCED_WIN, "XO. .X. ...", None),
    # X wins on a3 at once, without the faster win scoring it may take a longer way
    BoardPreset(texts.TTT_PRESET_FAST_WIN, "XO. X.. .O.", None),
)


# Parts of the file, one for each tab
FILE_KEYS = {"trees", "tictactoe"}

# Keys a tic-tac-toe position in the file may have
BOARD_PRESET_KEYS = {"board", "depth_limit", "prefer_fast"}


# Presets of both tabs: trees as pairs of name and text, tic-tac-toe positions as BoardPreset
@dataclass(frozen=True, slots=True)
class Presets:
    trees: list[tuple[str, str]]
    boards: list[BoardPreset]


# Built-in presets followed by the ones from the JSON file, if a path is given
# Trees are checked only when chosen, positions right here, a broken file stops the app on start
def load(path: str | None) -> Presets:
    presets = Presets(list(BUILT_IN), list(TICTACTOE_BUILT_IN))
    if path is None:
        return presets
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(texts.PRESETS_FILE_UNREADABLE.format(path=path, error=error)) from None

    # Unknown parts are refused too, so a typo in a key does not pass unnoticed
    trees = data.get("trees", {}) if isinstance(data, dict) else None
    boards = data.get("tictactoe", {}) if isinstance(data, dict) else None
    if (
        not isinstance(trees, dict)
        or not isinstance(boards, dict)
        or not set(data) <= FILE_KEYS
        or not all(isinstance(tree, str) for tree in trees.values())
    ):
        raise ValueError(texts.PRESETS_FILE_FORMAT.format(path=path))
    presets.trees.extend(trees.items())
    presets.boards.extend(_board_preset(path, name, value) for name, value in boards.items())
    return presets


# Tic-tac-toe preset from an object in the file
# Unknown keys are refused too, so a typo in a key does not pass unnoticed
def _board_preset(path: str, name: str, value: object) -> BoardPreset:
    if not isinstance(value, dict) or not isinstance(value.get("board"), str) or not set(value) <= BOARD_PRESET_KEYS:
        raise ValueError(texts.PRESETS_FILE_FORMAT.format(path=path))
    depth_limit = value.get("depth_limit")
    prefer_fast = value.get("prefer_fast", True)

    # bool is a kind of int in Python, so true must not pass as a depth limit
    depth_ok = depth_limit is None or (type(depth_limit) is int and depth_limit >= 1)
    if not depth_ok or not isinstance(prefer_fast, bool):
        raise ValueError(texts.PRESETS_FILE_FORMAT.format(path=path))

    # The position must be one the game accepts, the message says what is wrong with it
    try:
        TicTacToe(board_from_text(value["board"]))
    except ValueError as error:
        raise ValueError(texts.PRESETS_FILE_BOARD.format(path=path, name=name, error=error)) from None
    return BoardPreset(name, value["board"], depth_limit, prefer_fast)
