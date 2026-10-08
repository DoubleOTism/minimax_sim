"""
Game interface used by the search algorithms.

A game object holds the rules.
States are separate immutable values that the rules take in and give back.
"""

from collections.abc import Sequence
from typing import Protocol


# What every game must provide so that a search can be done
# S = Type of a game state
# M = Type of a move
class Game[S, M](Protocol):
    # Starting position
    def initial_state(self) -> S: ...

    # If MAX is on the move in this state
    def is_max_turn(self, state: S) -> bool: ...

    # Legal moves
    def moves(self, state: S) -> Sequence[M]: ...

    # State after the move, original state stays unchanged
    def apply(self, state: S, move: M) -> S: ...

    # If the game is over
    def is_terminal(self, state: S) -> bool: ...

    # Value of a finished game, depth is the number of moves made since the search root
    def utility(self, state: S, depth: int) -> float: ...

    # Estimated value of an unfinished game, used at depth limit
    def evaluate(self, state: S) -> float: ...

    # Text that is shown on the edge of the tree
    def move_label(self, move: M) -> str: ...
