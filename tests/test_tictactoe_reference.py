"""
Cross-check of tic-tac-toe against an independent reference written in this file.

The reference uses nothing from the project, no TicTacToe, no search, no events.
It works on a plain text of 9 characters "X", "O" or "." and has its own rules:
which positions can happen in a real game, when the game is over and what it is worth
with perfect play, a win is 10, with prefer_fast 10 + the empty cells, a draw is 0.
"""

import itertools
from functools import cache

import pytest

from minimax_sim.core.games.tictactoe import TicTacToe
from minimax_sim.core.search import alphabeta, minimax
from tests.helpers import board, run

# Rows, columns and diagonals, written out again so nothing comes from the project
REFERENCE_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Every possible filling of the 9 cells, 3 ** 9 = 19683 texts, most of them cannot happen in a game
ALL_BOARDS = ["".join(cells) for cells in itertools.product("XO.", repeat=9)]


# Marks that fill a whole line, both only in a position that cannot happen
def reference_winners(cells: str) -> set[str]:
    return {cells[a] for a, b, c in REFERENCE_LINES if cells[a] != "." and cells[a] == cells[b] == cells[c]}


# Whether the position can happen in a real game
# X starts and the players take turns, the game ends with the winning move, so the winner moved last
def reference_is_valid(cells: str) -> bool:
    x_count, o_count = cells.count("X"), cells.count("O")
    winners = reference_winners(cells)
    if x_count - o_count not in (0, 1) or len(winners) == 2:
        return False
    if winners == {"X"}:
        return x_count == o_count + 1
    if winners == {"O"}:
        return x_count == o_count
    return True


# Whether the game is over, somebody won or the board is full
def reference_is_over(cells: str) -> bool:
    return bool(reference_winners(cells)) or "." not in cells


# Value of a valid position for X with perfect play of both
@cache
def reference_value(cells: str, prefer_fast: bool) -> int:
    winners = reference_winners(cells)
    if winners:
        win = 10 + (cells.count(".") if prefer_fast else 0)
        return win if winners == {"X"} else -win
    if "." not in cells:
        return 0
    x_moves = cells.count("X") == cells.count("O")
    mark = "X" if x_moves else "O"
    values = [
        reference_value(cells[:cell] + mark + cells[cell + 1 :], prefer_fast)
        for cell in range(9)
        if cells[cell] == "."
    ]
    return max(values) if x_moves else min(values)


# The reference finds 5478 valid positions, the known number of positions reachable in tic-tac-toe
def test_reference_knows_all_reachable_positions():
    assert sum(reference_is_valid(cells) for cells in ALL_BOARDS) == 5478


# TicTacToe accepts exactly the positions the reference calls valid, and refuses all the others
# For the accepted ones it agrees on whether the game is over
def test_valid_positions_match_reference():
    for cells in ALL_BOARDS:
        try:
            game = TicTacToe(board(cells))
        except ValueError:
            assert not reference_is_valid(cells), cells
            continue
        assert reference_is_valid(cells), cells
        assert game.is_terminal(game.initial_state()) == reference_is_over(cells), cells


# Minimax and alpha-beta under both pruning rules give the reference value
# in every open position with 3 or 4 marks, the positions are chosen by the reference only
# Alpha-beta may skip nodes, but the value of the root must never change
@pytest.mark.parametrize("prefer_fast", [False, True])
def test_search_matches_reference_solver(prefer_fast):
    positions = [
        cells
        for cells in ALL_BOARDS
        if cells.count(".") in (5, 6) and reference_is_valid(cells) and not reference_is_over(cells)
    ]
    assert len(positions) > 1000
    for cells in positions:
        game = TicTacToe(board(cells), prefer_fast=prefer_fast)
        expected = reference_value(cells, prefer_fast)
        searches = [
            minimax(game, game.initial_state()),
            alphabeta(game, game.initial_state(), prune_on_equal=True),
            alphabeta(game, game.initial_state(), prune_on_equal=False),
        ]
        for search in searches:
            _, result = run(search)
            assert result.value == expected, cells


# The empty board is a draw, the well known result of tic-tac-toe
def test_empty_board_is_a_draw():
    assert reference_value("." * 9, prefer_fast=False) == 0
    assert reference_value("." * 9, prefer_fast=True) == 0