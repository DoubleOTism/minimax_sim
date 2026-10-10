"""
Tests for minimax and alpha-beta.
"""

from minimax_sim.core.events import Exit, Prune, ValueKind
from minimax_sim.core.search import alphabeta, minimax
from tests.helpers import leaves, principal_variation, prunes, run, visited


# Rosen's tree minimax
# Value 3, all 12 leaves visited, every value exact
def test_rosen_minimax(rosen):
    events, result = run(minimax(rosen, rosen.initial_state()))
    assert result.value == 3
    assert result.best_move == 0
    assert len(leaves(events)) == 12
    assert visited(events) == 26
    assert prunes(events) == 0
    assert all(e.kind is ValueKind.EXACT for e in events if isinstance(e, Exit))
    assert principal_variation(events) == (0, 0, 0, 0)


# Rosen's tree with alpha >= beta
# Same value, 6 leaves, exact values and bounds per node
def test_rosen_alphabeta_prune_on_equal(rosen):
    events, result = run(alphabeta(rosen, rosen.initial_state()))
    assert result.value == 3
    assert result.best_move == 0
    assert leaves(events) == [3, 17, 2, 15, 2, 3]
    assert principal_variation(events) == (0, 0, 0, 0)

    kinds = {e.node: (e.value, e.kind) for e in events if isinstance(e, Exit)}
    E, U, L = ValueKind.EXACT, ValueKind.UPPER, ValueKind.LOWER
    assert kinds == {
        (): (3, E),
        (0,): (3, E),
        (0, 0): (3, E),
        (0, 0, 0): (3, E),
        (0, 0, 1): (2, U),
        (0, 1): (15, L),
        (0, 1, 0): (15, E),
        (1,): (3, U),
        (1, 0): (3, U),
        (1, 0, 0): (2, U),
        (1, 0, 1): (3, E),
    }


# Rosen's tree with alpha > beta
# One prune less, 7 leaves
def test_rosen_alphabeta_prune_on_strict(rosen):
    events, result = run(alphabeta(rosen, rosen.initial_state(), prune_on_equal=False))
    assert result.value == 3
    assert len(leaves(events)) == 7
    assert principal_variation(events) == (0, 0, 0, 0)


# No Prune event when the bounds cross on the last child, nothing left to skip
def test_prune_only_when_moves_remain(rosen):
    events, _ = run(alphabeta(rosen, rosen.initial_state()))
    pruned = [e for e in events if isinstance(e, Prune)]
    assert all(p.node != (1, 0, 1) for p in pruned)
    assert all(p.skipped for p in pruned)
