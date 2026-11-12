"""
Tests for the explanation of the steps.

The expected sentences are built from the same texts, so the tests run in both languages.
"""

from minimax_sim import texts
from minimax_sim.core.events import Exit
from minimax_sim.core.games.abstract_tree import AbstractTree
from minimax_sim.core.games.tictactoe import TicTacToe
from minimax_sim.core.search import alphabeta, minimax
from minimax_sim.numbers import number_text
from minimax_sim.session.controller import Algorithm, Controller
from minimax_sim.session.narration import explain
from tests.helpers import board, run


# The abstract tree does not name its moves
def no_label(node):
    return ""


# Explanation of the step with the given number, counted from 1 like in the status bar
def step(events, number, show_bounds=True):
    return explain(events, number - 1, no_label, show_bounds)


# Alpha-beta on Rosen's tree: going down, a leaf, a bound, the prune and the way back up
def test_rosen_alphabeta_steps(rosen):
    events, _ = run(alphabeta(rosen, rosen.initial_state()))

    # The root has no parent, α and β start at the infinities
    root = texts.NARRATE_ENTER_ROOT.format(player=texts.PLAYER_MAX)
    assert step(events, 1) == root + " " + texts.NARRATE_BOUNDS_ROOT.format(alpha="-∞", beta="∞")

    # The first leaf goes back to its MIN parent, which takes it, then lowers beta
    leaf = texts.NARRATE_LEAF.format(value="3")
    assert step(events, 6) == leaf + " " + texts.NARRATE_PARENT_FIRST.format(parent=texts.PLAYER_MIN, value="3")
    assert step(events, 7) == texts.NARRATE_BETA.format(beta="3")

    # The second leaf is higher, MIN keeps 3
    keeps = texts.NARRATE_PARENT_KEEPS.format(
        parent=texts.PLAYER_MIN, goal=texts.GOAL_MIN, value="17", compare=texts.COMPARE_MORE, old="3"
    )
    assert step(events, 9) == texts.NARRATE_LEAF.format(value="17") + " " + keeps

    # MIN under a MAX that already has 3 gets a 2, α ≥ β and its last child is skipped
    assert step(events, 16) == texts.NARRATE_PRUNE_MIN.format(alpha="3", beta="2")

    # The pruned MIN leaves with a bound, it is lower and its MAX parent keeps 3
    exit_text = texts.NARRATE_EXIT_BOUND.format(player=texts.PLAYER_MIN, value="≤2")
    keeps = texts.NARRATE_PARENT_KEEPS.format(
        parent=texts.PLAYER_MAX, goal=texts.GOAL_MAX, value="2", compare=texts.COMPARE_LESS, old="3"
    )
    assert step(events, 17) == exit_text + " " + keeps

    # A MAX below a MIN that already has 3 gets 15 and is cut off
    assert step(events, 26) == texts.NARRATE_PRUNE_MAX.format(alpha="15", beta="3")

    # The last step names the value of the root
    assert step(events, len(events)) == texts.NARRATE_DONE.format(value="3")


# Minimax: no α and β, and a later higher child replaces the value of its MAX parent
def test_rosen_minimax_steps(rosen):
    events, _ = run(minimax(rosen, rosen.initial_state()))
    assert step(events, 1, show_bounds=False) == texts.NARRATE_ENTER_ROOT.format(player=texts.PLAYER_MAX)

    # Right subtree of the root: MAX under (1,) gets 2 from its first MIN child, then 3 from the second
    all_steps = [explain(events, i, no_label, False) for i in range(len(events))]
    expected = texts.NARRATE_PARENT_TAKES.format(
        parent=texts.PLAYER_MAX, goal=texts.GOAL_MAX, value="3", compare=texts.COMPARE_MORE, old="2"
    )
    assert any(text.endswith(expected) for text in all_steps)


# A MIN parent takes a lower value, and a value equal to the one it has changes nothing
def test_parent_takes_lower_and_ignores_equal():
    game = AbstractTree("(5 2 2)", root_is_max=False)
    events, _ = run(minimax(game, game.initial_state()))
    takes = texts.NARRATE_PARENT_TAKES.format(
        parent=texts.PLAYER_MIN, goal=texts.GOAL_MIN, value="2", compare=texts.COMPARE_LESS, old="5"
    )
    same = texts.NARRATE_PARENT_SAME.format(parent=texts.PLAYER_MIN, goal=texts.GOAL_MIN, value="2")
    leaf = texts.NARRATE_LEAF.format(value="2")
    assert step(events, 5, show_bounds=False) == leaf + " " + takes
    assert step(events, 7, show_bounds=False) == leaf + " " + same


# Tic-tac-toe names the move that leads into a node, a leaf at the depth limit is an estimate
def test_tictactoe_steps():
    game = TicTacToe(board("XO. X.. .O."))
    controller = Controller()
    controller.load(game, game.initial_state(), 1)
    assert controller.explanation() == texts.STEP_NOT_STARTED

    controller.set_algorithm(Algorithm.MINIMAX)
    controller.seek(1)
    assert controller.explanation() == texts.NARRATE_ENTER_MOVE.format(move="c1", player=texts.PLAYER_MIN, depth=1)

    # After X on c1 the lines open for X minus the lines open for O give 3, the MAX root takes it for now
    controller.seek(2)
    estimate = texts.NARRATE_LEAF_ESTIMATE_MOVE.format(move="c1", value="3")
    parent = texts.NARRATE_PARENT_FIRST.format(parent=texts.PLAYER_MAX, value="3")
    assert controller.explanation() == estimate + " " + parent


# A finished tic-tac-toe node is named by its move, three siblings with the same value can be told apart
def test_tictactoe_exit_names_the_move():
    game = TicTacToe(board("XO. X.. .O."))
    controller = Controller()
    controller.load(game, game.initial_state(), 2)
    controller.set_algorithm(Algorithm.MINIMAX)
    events, _ = run(minimax(game, game.initial_state(), 2))
    first_exit = next(i for i, event in enumerate(events) if isinstance(event, Exit) and event.node == (0,))
    controller.seek(first_exit)
    own = texts.NARRATE_EXIT_MOVE.format(player=texts.PLAYER_MIN, move="c1", value=number_text(events[first_exit].value))
    assert controller.explanation().startswith(own + " ")
