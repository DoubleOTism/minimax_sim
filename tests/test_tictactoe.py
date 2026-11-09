"""
Tests for tic-tac-toe and the search over it.
"""

import pytest

from minimax_sim.core.events import Leaf, LeafReason
from minimax_sim.core.games.tictactoe import TicTacToe, winner
from minimax_sim.core.search import alphabeta, minimax
from tests.helpers import board, leaves, principal_variation, run, visited


# Moves are the empty cells, players alternate, X is MAX
def test_game_interface():
    game = TicTacToe(board("X.. .O. ..."))
    state = game.initial_state()
    assert game.is_max_turn(state)
    assert game.moves(state) == [1, 2, 3, 5, 6, 7, 8]
    after = game.apply(state, 8)
    assert after == board("X.. .O. ..X")
    assert not game.is_max_turn(after)
    assert state == board("X.. .O. ...")
    assert game.move_label(0) == "a1"
    assert game.move_label(5) == "c2"
    assert game.move_label(7) == "b3"


# Rows, columns and diagonals win, a full board without a line is a draw
def test_terminal_and_winner():
    game = TicTacToe()
    assert winner(board("XXX OO. ...")) == "X"
    assert winner(board("O.X .OX ..O")) == "O"
    assert winner(board("XOX XOO OXX")) is None
    assert game.is_terminal(board("XOX XOO OXX"))
    assert not game.is_terminal(board("XO. ... ..."))


# A faster win is worth more, without prefer_fast every win is the same
def test_utility():
    fast, plain = TicTacToe(), TicTacToe(prefer_fast=False)
    assert fast.utility(board("XXX OO. ..."), 0) == 14
    assert fast.utility(board("XXX OOX XO."), 0) == 11
    assert plain.utility(board("XXX OO. ..."), 0) == 10
    assert fast.utility(board("XX. OOO X.."), 0) == -13
    assert fast.utility(board("XOX XOO OXX"), 0) == 0


# Heuristic: open lines for X minus open lines for O, center is the best first move
def test_evaluate():
    game = TicTacToe()
    assert game.evaluate(board("... .X. ...")) == 4
    assert game.evaluate(board("X.. ... ...")) == 3
    assert game.evaluate(board(".X. ... ...")) == 2


# Positions that cannot happen in a real game are refused
@pytest.mark.parametrize(
    "cells",
    [
        board("XX. ... ..."),
        board("O.. ... ..."),
        board("XXX OOO ..."),
        board("XXX OO. O.."),
        board("OOO XX. X.X"),
        ("X", "O"),
        board("XA. ... ..."),
    ],
)
def test_invalid_positions(cells):
    with pytest.raises(ValueError):
        TicTacToe(cells)


# X wins in one move, the search finds it, alpha-beta with far fewer nodes
def test_win_in_one():
    game = TicTacToe(board("XX. OO. ..."))
    events, result = run(minimax(game, game.initial_state()))
    assert result.value == 14
    assert game.moves(game.initial_state())[result.best_move] == 2
    assert visited(events) == 157

    events, result = run(alphabeta(game, game.initial_state()))
    assert result.value == 14
    assert visited(events) == 36


# Empty board ends in a draw, the counts match the reference from the old prototype
def test_empty_board_alphabeta():
    game = TicTacToe(prefer_fast=False)
    events, result = run(alphabeta(game, game.initial_state()))
    assert result.value == 0
    assert visited(events) == 18297
    assert len(leaves(events)) == 7330


# Depth limit 1 evaluates the 9 first moves with the heuristic and picks the center
def test_depth_limit_uses_heuristic():
    game = TicTacToe()
    events, result = run(minimax(game, game.initial_state(), depth_limit=1))
    assert result.value == 4
    assert game.moves(game.initial_state())[result.best_move] == 4
    assert leaves(events) == [3, 2, 3, 2, 4, 2, 3, 2, 3]
    assert all(e.reason is LeafReason.DEPTH_LIMIT for e in events if isinstance(e, Leaf))


# A mid game position, both algorithms agree on the draw and the optimal line
def test_mid_game_both_algorithms():
    game = TicTacToe(board("X.. .O. ..X"))
    minimax_events, minimax_result = run(minimax(game, game.initial_state()))
    alphabeta_events, alphabeta_result = run(alphabeta(game, game.initial_state()))
    assert minimax_result.value == alphabeta_result.value == 0
    assert principal_variation(minimax_events) == principal_variation(alphabeta_events)
    assert (visited(minimax_events), visited(alphabeta_events)) == (1053, 356)