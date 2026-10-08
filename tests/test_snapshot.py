"""
Tests for the tree state after a given step.
"""

from minimax_sim.core.events import Exit, Prune, ValueKind
from minimax_sim.core.search import alphabeta, minimax
from minimax_sim.session.snapshot import Snapshot, Status
from tests.helpers import run


# No events, no tree
def test_empty_snapshot():
    snap = Snapshot.build([], finished=False)
    assert snap.nodes == {} and snap.active is None and snap.path == ()
    assert snap.principal_variation == ()


# Statuses, bounds and values at three key moments of alpha-beta on Rosen's tree
def test_statuses_on_rosen(rosen):
    events, _ = run(alphabeta(rosen, rosen.initial_state()))

    # After entering (0,0,0): root, (0,) and (0,0) on the path, (0,0,0) active
    i = next(k for k, e in enumerate(events) if e.node == (0, 0, 0))
    snap = Snapshot.build(events[: i + 1], finished=False)
    assert snap.active == (0, 0, 0)
    assert snap.path == ((), (0,), (0, 0), (0, 0, 0))
    assert snap.nodes[()].status is Status.ON_PATH
    assert snap.nodes[(0, 0, 0)].status is Status.ACTIVE
    assert (snap.alpha, snap.beta) == (float("-inf"), float("inf"))

    # After the prune in (0,0,1): its second child is PRUNED, the first one DONE with value 2
    j = next(k for k, e in enumerate(events) if isinstance(e, Prune) and e.node == (0, 0, 1))
    snap = Snapshot.build(events[: j + 1], finished=False)
    assert snap.nodes[(0, 0, 1, 1)].status is Status.PRUNED
    assert snap.nodes[(0, 0, 1, 0)].status is Status.DONE
    assert snap.nodes[(0, 0, 1, 0)].value == 2
    assert (snap.alpha, snap.beta) == (3, 2)

    # After leaving (0,1): value 15 is only a lower bound, (0,) is active again
    k = next(k for k, e in enumerate(events) if isinstance(e, Exit) and e.node == (0, 1))
    snap = Snapshot.build(events[: k + 1], finished=False)
    assert snap.nodes[(0, 1)].status is Status.DONE
    assert snap.nodes[(0, 1)].value == 15 and snap.nodes[(0, 1)].kind is ValueKind.LOWER
    assert snap.active == (0,)


# The optimal line appears only once the run has finished
def test_principal_variation_only_when_finished(rosen):
    events, _ = run(minimax(rosen, rosen.initial_state()))
    assert Snapshot.build(events[:-1], finished=False).principal_variation == ()
    snap = Snapshot.build(events, finished=True)
    assert snap.principal_variation == ((), (0,), (0, 0), (0, 0, 0), (0, 0, 0, 0))
    assert snap.active is None
    assert all(n.status is Status.DONE for n in snap.nodes.values())


# Building the same prefix twice gives the same snapshot
def test_rebuild_is_deterministic(rosen):
    events, _ = run(alphabeta(rosen, rosen.initial_state()))
    for i in range(len(events)):
        assert Snapshot.build(events[: i + 1], finished=False) == Snapshot.build(events[: i + 1], finished=False)