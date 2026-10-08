"""
Emitted events by the search generators

Node is identified by the path of move indices from the root so node ids are independent of the concrete game

Examples on Rosen's tree:

    ()            root
    (0,)          first move from the root (left child)
    (1,)          second move from the root (right child)
    (0, 1)        first move from the root, then the second move
    (0, 0, 0, 0)  leftmost leaf, the 3

The index is the position in `game.moves(state)`.
"""

from dataclasses import dataclass
from enum import Enum


# Just a defined tuple not to repeat it till the end of the world everywhere
NodeId = tuple[int, ...]


# Why a node is a leaf
# Either game over or depth limit reached
class LeafReason(Enum):
    TERMINAL = "terminal"
    DEPTH_LIMIT = "depth_limit"


# If a node's value is exact or only a bound in case of pruning
#   UPPER  if value <= value
#   LOWER  if value >= value
class ValueKind(Enum):
    EXACT = "exact"
    UPPER = "upper"
    LOWER = "lower"


# Search entered a node, with the alpha/beta inherited from its parent
@dataclass(frozen=True, slots=True)
class Enter:
    node: NodeId
    depth: int
    is_max: bool
    alpha: float
    beta: float


# Node is a leaf and got its value
@dataclass(frozen=True, slots=True)
class Leaf:
    node: NodeId
    value: float
    reason: LeafReason


# Alpha or beta of a node changed
@dataclass(frozen=True, slots=True)
class BoundUpdate:
    node: NodeId
    alpha: float
    beta: float


# Remaining children of a node are skipped
#   skipped  indices of the moves that will not be explored, e.g. (1, 2)
@dataclass(frozen=True, slots=True)
class Prune:
    node: NodeId
    skipped: tuple[int, ...]


# Search left a node with its final value and best move
#   value      exact value, or only a bound if something below was pruned (see kind)
#   best_move  index into game.moves(state) of the move that gave the value
#   kind       EXACT, UPPER (value <= value) or LOWER (value >= value)
@dataclass(frozen=True, slots=True)
class Exit:
    node: NodeId
    value: float
    best_move: int | None
    kind: ValueKind


# Any of the events above
Event = Enter | Leaf | BoundUpdate | Prune | Exit
