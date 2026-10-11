"""
Positions of the tree nodes, computed once from the whole tree down to the depth limit.

Leaves get x = 0, 1, 2, ... from left to right, a parent sits centred above its children,
y is the depth. Units are abstract, the GUI converts them to pixels.
"""

from dataclasses import dataclass

from minimax_sim import config
from minimax_sim.core.events import NodeId
from minimax_sim.core.game import Game
from minimax_sim.core.search import is_leaf


# Position of one node
#   label     text on the edge from the parent, empty for the root
#   children  ids of the child nodes, empty for a leaf
@dataclass(frozen=True, slots=True)
class LayoutNode:
    node: NodeId
    x: float
    y: int
    is_max: bool
    label: str
    children: tuple[NodeId, ...]


# Positions of all nodes
#   width  number of leaves
#   depth  largest y
@dataclass(frozen=True, slots=True)
class Layout:
    nodes: dict[NodeId, LayoutNode]
    width: int
    depth: int


# Raised inside layout() to stop as soon as the tree has too many nodes
class _TooBig(Exception):
    pass


# Lay out the whole tree, or return None if it has more than max_nodes nodes
def layout(game: Game, state, depth_limit: int | None, max_nodes: int = config.MAX_DRAWN_NODES) -> Layout | None:
    nodes: dict[NodeId, LayoutNode] = {}
    next_leaf_x = 0
    node_count = 0

    # Place the subtree of one node, return the node's x
    def visit(node_state, node: NodeId, depth: int, label: str) -> float:
        nonlocal next_leaf_x, node_count
        node_count += 1
        if node_count > max_nodes:
            raise _TooBig

        moves = [] if is_leaf(game, node_state, depth, depth_limit) else game.moves(node_state)
        child_xs = [
            visit(game.apply(node_state, move), node + (i,), depth + 1, game.move_label(move))
            for i, move in enumerate(moves)
        ]

        # A leaf takes the next free x, a parent sits in the middle above its children
        if child_xs:
            x = (child_xs[0] + child_xs[-1]) / 2
        else:
            x = next_leaf_x
            next_leaf_x += 1

        children = tuple(node + (i,) for i in range(len(moves)))
        nodes[node] = LayoutNode(node, x, depth, game.is_max_turn(node_state), label, children)
        return x

    try:
        visit(state, (), 0, "")
    except _TooBig:
        return None
    return Layout(nodes, next_leaf_x, max(n.y for n in nodes.values()))
