"""
Tests for the tree presets and the JSON file with extra ones.
"""

import json

import pytest

from minimax_sim import presets, texts
from minimax_sim.core.games.abstract_tree import AbstractTree
from minimax_sim.core.games.tictactoe import TicTacToe, board_from_text
from minimax_sim.core.search import alphabeta, minimax
from minimax_sim.session.layout import layout
from tests.helpers import leaves, principal_variation, prunes, run


# Every built-in preset is a valid tree
def test_built_in_presets_parse():
    for _, tree in presets.BUILT_IN:
        AbstractTree(tree)


# Best order: alpha-beta evaluates only 7 of 16 leaves
# Worst order: the same leaves, nothing pruned under either pruning rule
def test_move_order_presets():
    best = AbstractTree(presets.BEST_ORDER_TREE)
    events, result = run(alphabeta(best, best.initial_state()))
    assert result.value == 14
    assert len(leaves(events)) == 7

    worst = AbstractTree(presets.WORST_ORDER_TREE)
    for prune_on_equal in (True, False):
        events, result = run(alphabeta(worst, worst.initial_state(), prune_on_equal=prune_on_equal))
        assert result.value == 14
        assert len(leaves(events)) == 16
        assert prunes(events) == 0

    # Both trees have the same leaves, only in a different order
    best_leaves = leaves(run(minimax(best, best.initial_state()))[0])
    worst_leaves = leaves(run(minimax(worst, worst.initial_state()))[0])
    assert sorted(best_leaves) == sorted(worst_leaves)


# Without a file only the built-in presets are offered
def test_no_file_gives_built_in_only():
    loaded = presets.load(None)
    assert loaded.trees == list(presets.BUILT_IN)
    assert loaded.boards == list(presets.TICTACTOE_BUILT_IN)


# Presets from the file come after the built-in ones, in the file order
def test_file_presets_are_appended(tmp_path):
    path = tmp_path / "presets.json"
    content = {
        "trees": {"A": "((1 2) (3))", "B": "(5 6)"},
        "tictactoe": {
            "Corners": {"board": "X.. .O. ..X", "depth_limit": None},
            "Empty": {"board": "... ... ...", "depth_limit": 2, "prefer_fast": False},
        },
    }
    path.write_text(json.dumps(content), encoding="utf-8")
    loaded = presets.load(str(path))
    assert loaded.trees[: len(presets.BUILT_IN)] == list(presets.BUILT_IN)
    assert loaded.trees[len(presets.BUILT_IN) :] == [("A", "((1 2) (3))"), ("B", "(5 6)")]
    assert loaded.boards[len(presets.TICTACTOE_BUILT_IN) :] == [
        presets.BoardPreset("Corners", "X.. .O. ..X", None, True),
        presets.BoardPreset("Empty", "... ... ...", 2, False),
    ]


# Each part may be left out
def test_file_with_one_part(tmp_path):
    path = tmp_path / "presets.json"
    path.write_text(json.dumps({"tictactoe": {"Empty": {"board": "... ... ..."}}}), encoding="utf-8")
    loaded = presets.load(str(path))
    assert loaded.trees == list(presets.BUILT_IN)
    assert loaded.boards[-1] == presets.BoardPreset("Empty", "... ... ...", None, True)


# A missing file, broken JSON, a wrong structure or a position the game refuses
# Stop the app with a clear message
@pytest.mark.parametrize(
    "content",
    [
        None,
        "{not json",
        '["((1 2))"]',
        '{"A": "((1 2))"}',
        '{"trees": ["((1 2))"]}',
        '{"trees": {"A": 3}}',
        '{"tictactoe": {"A": "... ... ..."}}',
        '{"tictactoe": {"A": {"depth_limit": 2}}}',
        '{"tictactoe": {"A": {"board": "... ... ...", "depth": 2}}}',
        '{"tictactoe": {"A": {"board": "... ... ...", "depth_limit": 0}}}',
        '{"tictactoe": {"A": {"board": "... ... ...", "depth_limit": true}}}',
        '{"tictactoe": {"A": {"board": "... ... ...", "prefer_fast": "yes"}}}',
        '{"tictactoe": {"A": {"board": "XX. ... ..."}}}',
        '{"tictactoe": {"A": {"board": "X.."}}}',
    ],
)
def test_bad_file_is_reported(tmp_path, content):
    path = tmp_path / "presets.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="presets.json"):
        presets.load(str(path))


# Every tic-tac-toe preset is a valid position and its tree can be drawn
def test_tictactoe_presets_can_be_drawn():
    for preset in presets.TICTACTOE_BUILT_IN:
        game = TicTacToe(board_from_text(preset.board), prefer_fast=preset.prefer_fast)
        assert layout(game, game.initial_state(), preset.depth_limit) is not None, preset.name


# The faster win preset: X wins at once, without the faster win scoring the optimal line is longer
def test_fast_win_preset():
    fast_win = next(p for p in presets.TICTACTOE_BUILT_IN if p.name == texts.TTT_PRESET_FAST_WIN)
    lengths = []
    for prefer_fast in (True, False):
        game = TicTacToe(board_from_text(fast_win.board), prefer_fast=prefer_fast)
        events, _ = run(minimax(game, game.initial_state()))
        lengths.append(len(principal_variation(events)))
    assert lengths[0] == 1 and lengths[1] > 1


# The worst order tree is the best order tree mirrored, so right to left they swap
# Best order then prunes nothing and worst order evaluates only 7 of the 16 leaves
def test_move_order_presets_right_to_left():
    best = AbstractTree(presets.BEST_ORDER_TREE)
    events, _ = run(alphabeta(best, best.initial_state(), right_to_left=True))
    assert len(leaves(events)) == 16
    assert prunes(events) == 0

    worst = AbstractTree(presets.WORST_ORDER_TREE)
    events, _ = run(alphabeta(worst, worst.initial_state(), right_to_left=True))
    assert len(leaves(events)) == 7
