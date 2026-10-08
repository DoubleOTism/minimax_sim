"""
Abstract game tree given as text in Rosen's format, something like:

    ( (((3 17) (2 12)) ((15) (25 0))) (((2 5) (3)) ((2 14))) )

An inner node is a parenthesised list of children, a leaf is a number.

The root is MAX and levels alternate.
A move is the child index.
"""

import math
from dataclasses import dataclass

from minimax_sim import texts

# A tree is either a number (leaf) or a tuple of trees (inner node)
type Tree = float | tuple["Tree", ...]


# Parsing error that remembers where in the text it happened
class ParseError(ValueError):
    def __init__(self, message: str, pos: int) -> None:
        super().__init__(message)
        self.pos = pos


# Text in Rosen's format to nested tuples of numbers
def parse(text: str) -> Tree:
    pos = 0
    length = len(text)

    # Move positions past spaces and newlines
    def skip_ws() -> None:
        nonlocal pos
        while pos < length and text[pos].isspace():
            pos += 1

    # Read one node starting at pos: either "( ... )" or a number
    def node() -> Tree:
        nonlocal pos
        skip_ws()
        if pos >= length:
            raise ParseError(texts.PARSE_EMPTY_INPUT, pos)

        char = text[pos]

        # Inner node: read children until the matching ")"
        if char == "(":
            list_start = pos
            pos += 1
            children: list[Tree] = []
            while True:
                skip_ws()
                if pos >= length:
                    raise ParseError(texts.PARSE_MISSING_CLOSE.format(pos=list_start), list_start)
                if text[pos] == ")":
                    pos += 1
                    break
                # Recursion as each child can be a whole subtree
                children.append(node())
            if not children:
                raise ParseError(texts.PARSE_EMPTY_LIST.format(pos=list_start), list_start)
            return tuple(children)

        # ")" here means there is no "(" it could close
        if char == ")":
            raise ParseError(texts.PARSE_UNEXPECTED_CLOSE.format(pos=pos), pos)

        # Leaf, collect the characters of one number
        number_start = pos
        while pos < length and (text[pos].isalnum() or text[pos] in "+-."):
            pos += 1
        number_text = text[number_start:pos]

        # Whole numbers stay int (3, not 3.0), everything else goes through float
        try:
            value = int(number_text) if number_text.lstrip("+-").isdigit() else float(number_text)
        except ValueError:
            raise ParseError(
                texts.PARSE_UNEXPECTED_CHAR.format(char=char, pos=number_start), number_start
            ) from None

        # A dirty fix that works
        # float() accepts "inf" and "nan", which are not valid leaf values
        # Throw an error
        if not math.isfinite(value):
            raise ParseError(
                texts.PARSE_NOT_FINITE.format(token=number_text, pos=number_start), number_start
            )
        return value

    # The whole text must be exactly one tree, nothing after it
    tree = node()
    skip_ws()
    if pos < length:
        raise ParseError(texts.PARSE_TRAILING.format(pos=pos), pos)
    return tree


# Game state: where in the tree we are and who moves
@dataclass(frozen=True, slots=True)
class TreeState:
    node: Tree
    is_max: bool


# Rules of the abstract tree game
class AbstractTree:
    # Accepts the text in Rosen's format, or an already parsed tree
    def __init__(self, tree: Tree | str) -> None:
        self.tree = parse(tree) if isinstance(tree, str) else tree

    # The whole tree, MAX on the move
    def initial_state(self) -> TreeState:
        return TreeState(self.tree, True)

    # Who moves is stored in the state, it flips on every move
    def is_max_turn(self, state: TreeState) -> bool:
        return state.is_max

    # One move per child (0, 1, 2, ...), leaf has no moves
    def moves(self, state: TreeState) -> range:
        return range(len(state.node)) if isinstance(state.node, tuple) else range(0)

    # Go down to the chosen child, the other player moves
    def apply(self, state: TreeState, move: int) -> TreeState:
        return TreeState(state.node[move], not state.is_max)

    # A number means a leaf, the game ends there
    def is_terminal(self, state: TreeState) -> bool:
        return not isinstance(state.node, tuple)

    # The value of a leaf is its number, depth does not matter here
    def utility(self, state: TreeState, depth: int) -> float:
        return state.node

    # Leaf numbers already are the evaluated values, there is nothing to estimate
    def evaluate(self, state: TreeState) -> float:
        raise NotImplementedError(texts.TREE_NO_HEURISTIC)

    # Edge label is just the child index
    def move_label(self, move: int) -> str:
        return str(move)
