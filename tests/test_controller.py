"""
Tests for stepping through a run.
"""

import pytest

from minimax_sim import config, texts
from minimax_sim.core.games.abstract_tree import AbstractTree
from minimax_sim.session.controller import Algorithm, Controller


# Controller with Rosen's tree loaded, stepping through alpha-beta
@pytest.fixture
def ctl(rosen):
    controller = Controller()
    controller.load(rosen, rosen.initial_state())
    controller.set_algorithm(Algorithm.ALPHABETA)
    return controller


# Stepping forward to the end and back again gives the same snapshots
def test_fine_steps_round_trip(ctl):
    assert ctl.position == -1 and not ctl.can_step_back and ctl.can_step_forward
    snapshots = [ctl.snapshot()]
    while ctl.can_step_forward:
        ctl.step_forward()
        snapshots.append(ctl.snapshot())
    assert ctl.position == 46
    assert ctl.snapshot().principal_variation == ((), (0,), (0, 0), (0, 0, 0), (0, 0, 0, 0))
    for expected in reversed(snapshots[:-1]):
        ctl.step_back()
        assert ctl.snapshot() == expected
    assert ctl.position == -1


# Seeking stays inside the run
def test_seek_is_clamped(ctl):
    ctl.to_end()
    end = ctl.position
    assert end == 46 and not ctl.can_step_forward and ctl.total_steps == 47
    ctl.seek(end + 50)
    assert ctl.position == end
    ctl.seek(-10)
    assert ctl.position == -1
    ctl.step_back()
    assert ctl.position == -1


# Total steps are unknown until the run has been read to the end
def test_total_steps_known_only_at_the_end(ctl):
    assert ctl.total_steps is None
    ctl.to_end()
    assert ctl.total_steps == 47


# The last step reached by single steps shows the optimal line right away,
# without asking if it can_step_forward first
def test_last_step_knows_it_is_last(ctl):
    for _ in range(47):
        ctl.step_forward()
    assert ctl.position == 46
    assert ctl.total_steps == 47
    assert ctl.snapshot().principal_variation == ((), (0,), (0, 0), (0, 0, 0), (0, 0, 0, 0))


# Changing the algorithm or the pruning convention starts the run again
def test_settings_restart_the_run(ctl):
    ctl.to_end()
    ctl.set_algorithm(Algorithm.MINIMAX)
    assert ctl.position == -1
    ctl.to_end()
    assert ctl.total_steps == 52

    ctl.set_algorithm(Algorithm.ALPHABETA)
    ctl.set_prune_on_equal(False)
    assert ctl.position == -1
    ctl.to_end()
    assert ctl.total_steps == 55


# A tree bigger than the drawing limit has no layout and a message instead
def test_tree_too_big():
    wide = AbstractTree("(" + " ".join("1" for _ in range(config.MAX_DRAWN_NODES)) + ")")
    controller = Controller()
    controller.load(wide, wide.initial_state())
    assert controller.layout() is None
    assert controller.layout_error == texts.TREE_TOO_BIG.format(limit=config.MAX_DRAWN_NODES)
