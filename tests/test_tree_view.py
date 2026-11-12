"""
Tests for drawing the tree.

The tree is drawn whole once and then only changed step by step,
so after any steps it must look the same as a tree drawn from scratch at that step.
The scenes are compared as pictures.
"""

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter

from minimax_sim import texts
from minimax_sim.core.games.tictactoe import TicTacToe
from minimax_sim.gui.tree_source import TreeSource
from minimax_sim.gui.tree_view import OPTIMAL_LINE_COLOR, TreeView
from minimax_sim.session.controller import Algorithm, Controller
from tests.helpers import board


# The whole scene rendered into an image of its own size
def picture(view: TreeView) -> QImage:
    rect = view.scene().sceneRect()
    image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    view.scene().render(painter, QRectF(image.rect()), rect)
    painter.end()
    return image


# Rosen's tree and a tic-tac-toe position with move labels, both algorithms,
# every step forward, then jumps back and forth, with and without hidden unvisited nodes
@pytest.mark.parametrize("algorithm", list(Algorithm))
@pytest.mark.parametrize("hide_unvisited", [False, True])
@pytest.mark.parametrize("game_name", ["rosen", "tictactoe"])
def test_steps_look_like_a_fresh_drawing(qt_app, rosen, algorithm, hide_unvisited, game_name):
    game = rosen if game_name == "rosen" else TicTacToe(board("XOX .O. X.."))
    controller = Controller()
    controller.load(game, game.initial_state())
    controller.set_algorithm(algorithm)
    controller.to_end()
    last = controller.total_steps - 1
    show_bounds = algorithm is Algorithm.ALPHABETA

    stepped = TreeView()
    stepped.hide_unvisited = hide_unvisited
    for position in [*range(-1, last + 1), last // 2, 3, last, -1, last // 3]:
        controller.seek(position)
        stepped.draw(controller.layout(), controller.snapshot(), show_bounds)
        fresh = TreeView()
        fresh.hide_unvisited = hide_unvisited
        fresh.draw(controller.layout(), controller.snapshot(), show_bounds)
        assert picture(stepped) == picture(fresh), position


# A different tree is drawn whole again, nothing from the old one stays
def test_new_tree_replaces_the_old_one(qt_app, rosen):
    view = TreeView()
    controller = Controller()
    controller.load(rosen, rosen.initial_state())
    controller.to_end()
    view.draw(controller.layout(), controller.snapshot(), False)

    game = TicTacToe(board("XOX .O. X.."))
    controller.load(game, game.initial_state())
    view.draw(controller.layout(), controller.snapshot(), False)
    fresh = TreeView()
    fresh.draw(controller.layout(), controller.snapshot(), False)
    assert picture(view) == picture(fresh)


# After the last step the optimal line is green, nodes and the edges leading to them
# The comparison above only checks that stepping and drawing anew agree, this checks the colour itself
def test_optimal_line_is_green(qt_app, rosen):
    controller = Controller()
    controller.load(rosen, rosen.initial_state())
    controller.to_end()
    view = TreeView()
    view.draw(controller.layout(), controller.snapshot(), False)
    green = QColor(OPTIMAL_LINE_COLOR)
    for node in controller.snapshot().principal_variation[1:]:
        assert view._edges[node].pen().color() == green
        assert view._shapes[node].pen().color() == green


# The bubble over a node of the abstract tree describes it: who moves and the leaves below, or the leaf value
# A large subtree lists only the first leaves and the count
def test_tree_source_describes_nodes(qt_app, rosen):
    source = TreeSource([("Rosen", "((3 17) (2 12))")])
    controller = Controller()
    controller.load(rosen, rosen.initial_state())

    assert source.node_tooltip(controller.node_state(()), None, 0).split("<br>") == [
        texts.TREE_NODE_MAX.format(children=2),
        texts.TREE_NODE_DEPTH.format(depth=0),
        texts.TREE_NODE_LEAVES.format(values=texts.TREE_NODE_MORE_LEAVES.format(values="3, 17, 2, 12, 15, 25, 0, 2", count=12)),
    ]

    lines = source.node_tooltip(controller.node_state((0, 0, 0)), 0, 3).split("<br>")
    assert lines[2] == texts.TREE_NODE_LEAVES.format(values="3, 17")

    leaf = (0, 0, 0, 1)
    assert source.node_tooltip(controller.node_state(leaf), 1, 4) == texts.TREE_NODE_LEAF.format(value="17", depth=4)
