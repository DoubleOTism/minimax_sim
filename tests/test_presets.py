"""
Tests for the tree presets and the JSON file with extra ones.
"""

import json

import pytest

from minimax_sim import presets
from minimax_sim.core.games.abstract_tree import AbstractTree
from minimax_sim.core.search import alphabeta, minimax
from tests.helpers import leaves, prunes, run


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
    assert presets.load(None) == list(presets.BUILT_IN)


# Presets from the file come after the built-in ones, in the file order
def test_file_presets_are_appended(tmp_path):
    path = tmp_path / "presets.json"
    path.write_text(json.dumps({"A": "((1 2) (3))", "B": "(5 6)"}), encoding="utf-8")
    loaded = presets.load(str(path))
    assert loaded[: len(presets.BUILT_IN)] == list(presets.BUILT_IN)
    assert loaded[len(presets.BUILT_IN) :] == [("A", "((1 2) (3))"), ("B", "(5 6)")]


# A missing file, broken JSON or values that are not text stop the app with a clear message
@pytest.mark.parametrize(
    "content",
    [None, "{not json", '["((1 2))"]', '{"A": 3}'],
)
def test_bad_file_is_reported(tmp_path, content):
    path = tmp_path / "presets.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="presets.json"):
        presets.load(str(path))