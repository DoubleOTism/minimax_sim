"""
Tests for the abstract tree game and its parser.
"""

import pytest

from minimax_sim.core.games.abstract_tree import AbstractTree, ParseError, TreeState, parse
from tests.conftest import ROSEN


# Rosen's example tree parses into the expected nested tuples
def test_parse_rosen():
    assert parse(ROSEN) == (
        (((3, 17), (2, 12)), ((15,), (25, 0))),
        (((2, 5), (3,)), ((2, 14),)),
    )


# Extra whitespace, signs, decimals and a single number as a whole tree
@pytest.mark.parametrize(
    "text, expected",
    [
        ("((3 17)(2 12))", ((3, 17), (2, 12))),
        ("  ( -1 2.5 +3 )  ", (-1, 2.5, 3)),
        ("7", 7),
    ],
)
def test_parse_variants(text, expected):
    assert parse(text) == expected


# Invalid input raises ParseError pointing at the right position
@pytest.mark.parametrize(
    "text, pos",
    [
        ("", 0),  # empty input
        ("   ", 3),  # only whitespace
        ("(3 17", 0),  # missing ")"
        ("(3 (17)", 0),  # missing outer ")"
        ("3)", 1),  # unexpected ")"
        ("(3) 4", 4),  # text after the tree
        ("(3 x)", 3),  # not a number
        ("()", 0),  # empty list
        ("(3 ())", 3),  # empty inner list
    ],
)
def test_parse_errors_report_position(text, pos):
    with pytest.raises(ParseError) as info:
        parse(text)
    assert info.value.pos == pos
    assert str(pos) in str(info.value) or text.strip() == ""


# inf and nan are accepted by float(), but are not valid leaf values
@pytest.mark.parametrize(
    "text, pos",
    [
        ("(inf 2)", 1),
        ("(nan 1)", 1),
        ("(1 -infinity)", 3),
    ],
)
def test_parse_rejects_non_finite(text, pos):
    with pytest.raises(ParseError) as info:
        parse(text)
    assert info.value.pos == pos


# Moves, apply, alternating MAX/MIN, leaves, values and labels
def test_game_interface():
    game = AbstractTree("((1 2) (3))")
    root = game.initial_state()
    assert root == TreeState(((1, 2), (3,)), True)
    assert list(game.moves(root)) == [0, 1]
    child = game.apply(root, 1)
    assert child == TreeState((3,), False)
    assert not game.is_max_turn(child)
    leaf = game.apply(child, 0)
    assert game.is_terminal(leaf) and not game.is_terminal(child)
    assert game.utility(leaf, 2) == 3
    assert game.move_label(1) == "1"


# The abstract tree has no heuristic, so a depth limit must fail loudly
def test_evaluate_is_unsupported():
    game = AbstractTree("((1 2) (3))")
    with pytest.raises(NotImplementedError):
        game.evaluate(game.initial_state())
