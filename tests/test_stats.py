from minimax_sim.core.games.abstract_tree import AbstractTree
from minimax_sim.presets import ROSEN_TREE
from minimax_sim.session.controller import Algorithm, Controller


# Controller with Rosen's tree and the given pruning rule
def _rosen(prune_on_equal: bool = True) -> Controller:
    game = AbstractTree(ROSEN_TREE)
    controller = Controller()
    controller.load(game, game.initial_state())
    controller.set_prune_on_equal(prune_on_equal)
    return controller


def test_minimax_visits_whole_tree():
    stats = _rosen().stats()[Algorithm.MINIMAX]
    assert (stats.nodes, stats.leaves, stats.pruned, stats.steps) == (26, 12, 0, 52)


def test_alphabeta_saves_work_on_rosen():
    stats = _rosen().stats()[Algorithm.ALPHABETA]
    assert stats.leaves == 6
    assert stats.steps == 47
    assert stats.nodes < 26


def test_stats_follow_pruning_rule():
    controller = _rosen()
    with_equal = controller.stats()[Algorithm.ALPHABETA]
    controller.set_prune_on_equal(False)
    without_equal = controller.stats()[Algorithm.ALPHABETA]
    assert without_equal.steps == 55
    assert without_equal.leaves > with_equal.leaves


def test_stats_do_not_depend_on_stepping():
    controller = _rosen()
    before = controller.stats()
    controller.step_forward()
    controller.to_end()
    assert controller.stats() == before
