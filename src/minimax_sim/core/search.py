"""
Minimax and alpha-beta as recursive generators.

Each generator yields events (see events.py) and returns a SearchResult
at the end. Leaves emit Enter + Leaf, inner nodes emit Enter ... Exit.
"""

from collections.abc import Generator
from dataclasses import dataclass
from math import inf

from .events import Enter, Event, Exit, Leaf, LeafReason, NodeId, ValueKind, BoundUpdate, Prune
from .game import Game


# Final answer of a search
# Value of the root and which move leads there
#   best_move  index into game.moves(state). None if the root is a leaf
@dataclass(frozen=True, slots=True)
class SearchResult:
    value: float
    best_move: int | None


# A search yields events and returns a SearchResult when it finishes
type Search = Generator[Event, None, SearchResult]


# Whether the search stops at this node, the game is over, or the depth limit is reached
def is_leaf(game: Game, state, depth: int, depth_limit: int | None) -> bool:
    return game.is_terminal(state) or (depth_limit is not None and depth >= depth_limit)


# Value and reason if the node is a leaf, None if the search goes deeper
def _leaf_value(game: Game, state, depth: int, depth_limit: int | None) -> tuple[float, LeafReason] | None:
    if not is_leaf(game, state, depth, depth_limit):
        return None
    if game.is_terminal(state):
        return game.utility(state, depth), LeafReason.TERMINAL
    return game.evaluate(state), LeafReason.DEPTH_LIMIT


# Strictly better only, so on a tie the first move stays the best
def _better(value: float, best: float, is_max: bool) -> bool:
    return value > best if is_max else value < best


###
# Minimax
###

# Plain minimax from the given state, no pruning
def minimax(game: Game, state, depth_limit: int | None = None) -> Search:
    return (yield from _minimax(game, state, depth_limit, (), 0))


def _minimax(game: Game, state, depth_limit: int | None, node: NodeId, depth: int) -> Search:
    is_max = game.is_max_turn(state)
    yield Enter(node, depth, is_max, -inf, inf)

    # Leaf: report its value and go back up
    if (leaf := _leaf_value(game, state, depth, depth_limit)) is not None:
        value, reason = leaf
        yield Leaf(node, value, reason)
        return SearchResult(value, None)

    # Inner node: try every move, MAX keeps the highest value, MIN the lowest
    best_value = -inf if is_max else inf
    best_move = None
    for i, move in enumerate(game.moves(state)):
        child = yield from _minimax(
            game, game.apply(state, move), depth_limit, node + (i,), depth + 1
        )
        if best_move is None or _better(child.value, best_value, is_max):
            best_value, best_move = child.value, i

    yield Exit(node, best_value, best_move, ValueKind.EXACT)
    return SearchResult(best_value, best_move)


###
# Alpha-beta
###

# Alpha-beta from the given state, prunes on alpha >= beta (or alpha > beta)
def alphabeta(
    game: Game, state, depth_limit: int | None = None, *, prune_on_equal: bool = True
) -> Search:
    result, _pruned = yield from _alphabeta(
        game, state, depth_limit, (), 0, -inf, inf, prune_on_equal
    )
    return result


# Fail-soft alpha-beta, returns (result, whether anything below was pruned)
def _alphabeta(
    game: Game,
    state,
    depth_limit: int | None,
    node: NodeId,
    depth: int,
    alpha: float,
    beta: float,
    prune_on_equal: bool,
) -> Generator[Event, None, tuple[SearchResult, bool]]:
    is_max = game.is_max_turn(state)
    yield Enter(node, depth, is_max, alpha, beta)

    # Leaf: report its value and go back up
    if (leaf := _leaf_value(game, state, depth, depth_limit)) is not None:
        value, reason = leaf
        yield Leaf(node, value, reason)
        return SearchResult(value, None), False

    # Bounds on entry, decide later if the value is exact
    alpha_orig, beta_orig = alpha, beta
    best_value = -inf if is_max else inf
    best_move = None
    pruned = False
    moves = game.moves(state)

    for i, move in enumerate(moves):
        child, child_pruned = yield from _alphabeta(
            game,
            game.apply(state, move),
            depth_limit,
            node + (i,),
            depth + 1,
            alpha,
            beta,
            prune_on_equal,
        )
        pruned = pruned or child_pruned
        if best_move is None or _better(child.value, best_value, is_max):
            best_value, best_move = child.value, i

        # MAX raises alpha, MIN lowers beta
        if is_max and best_value > alpha:
            alpha = best_value
            yield BoundUpdate(node, alpha, beta)
        elif not is_max and best_value < beta:
            beta = best_value
            yield BoundUpdate(node, alpha, beta)

        # Bounds crossed: the remaining moves cannot change the result
        cutoff = alpha >= beta if prune_on_equal else alpha > beta
        if cutoff and i < len(moves) - 1:
            yield Prune(node, tuple(range(i + 1, len(moves))))
            pruned = True
            break

    # Exact if nothing below was pruned or the value lies inside the entry bounds
    if not pruned or alpha_orig < best_value < beta_orig:
        kind = ValueKind.EXACT
    elif best_value <= alpha_orig:
        kind = ValueKind.UPPER
    else:
        kind = ValueKind.LOWER

    yield Exit(node, best_value, best_move, kind)
    return SearchResult(best_value, best_move), pruned
