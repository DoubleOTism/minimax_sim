"""
Explanation of one step of the search in plain words.

A step is one event. The text says what happened in it and, when a child
finishes, what its parent does with the value on the way back up.
Everything is read from the events before the step, so it works for any game
and in both directions of the search.
"""

from collections.abc import Callable, Iterator, Sequence

from minimax_sim import texts
from minimax_sim.core.events import (
    BoundUpdate,
    Enter,
    Event,
    Exit,
    Leaf,
    LeafReason,
    NodeId,
    Prune,
    ValueKind,
)
from minimax_sim.numbers import number_text, value_text


# Text for the event at index
#   move_label   name of the move that leads to a node, empty when the game has none
#                the texts then name the node by its move, so it can be found in the tree
#   show_bounds  alpha-beta, α and β are mentioned when entering a node
def explain(events: Sequence[Event], index: int, move_label: Callable[[NodeId], str], show_bounds: bool) -> str:
    event = events[index]
    match event:
        case Enter():
            return _explain_enter(event, move_label, show_bounds)
        case Leaf(node=node, value=value, reason=reason):
            label = move_label(node) if node else ""
            if reason is LeafReason.DEPTH_LIMIT:
                own = texts.NARRATE_LEAF_ESTIMATE_MOVE if label else texts.NARRATE_LEAF_ESTIMATE
            else:
                own = texts.NARRATE_LEAF_MOVE if label else texts.NARRATE_LEAF
            return _with_parent(own.format(move=label, value=number_text(value)), events, index, node, value)
        case BoundUpdate(node=node, alpha=alpha, beta=beta):
            if _enter_of(events, index, node).is_max:
                return texts.NARRATE_ALPHA.format(alpha=number_text(alpha))
            return texts.NARRATE_BETA.format(beta=number_text(beta))
        case Prune(node=node):
            return _explain_prune(events, index, node)
        case Exit(node=node, value=value, kind=kind):
            if node == ():
                return texts.NARRATE_DONE.format(value=value_text(value, kind))
            label = move_label(node)
            if kind is ValueKind.EXACT:
                own = texts.NARRATE_EXIT_MOVE if label else texts.NARRATE_EXIT
            else:
                own = texts.NARRATE_EXIT_BOUND_MOVE if label else texts.NARRATE_EXIT_BOUND
            player = _player(_enter_of(events, index, node).is_max)
            text = own.format(move=label, player=player, value=value_text(value, kind))
            return _with_parent(text, events, index, node, value)


# Going down into a node, with the move that leads there and α, β from the parent
def _explain_enter(event: Enter, move_label: Callable[[NodeId], str], show_bounds: bool) -> str:
    player = _player(event.is_max)
    if event.node == ():
        text = texts.NARRATE_ENTER_ROOT.format(player=player)
    elif label := move_label(event.node):
        text = texts.NARRATE_ENTER_MOVE.format(move=label, player=player, depth=event.depth)
    else:
        text = texts.NARRATE_ENTER.format(player=player, depth=event.depth)
    if show_bounds:
        bounds = texts.NARRATE_BOUNDS_ROOT if event.node == () else texts.NARRATE_BOUNDS
        text += " " + bounds.format(alpha=number_text(event.alpha), beta=number_text(event.beta))
    return text


# α reached β, the rest of the children cannot change the result above
def _explain_prune(events: Sequence[Event], index: int, node: NodeId) -> str:
    alpha, beta = _bounds_of(events, index, node)
    template = texts.NARRATE_PRUNE_MAX if _enter_of(events, index, node).is_max else texts.NARRATE_PRUNE_MIN
    return template.format(alpha=number_text(alpha), beta=number_text(beta))


# Text of a finished child followed by what its parent does with the value
# The root has no parent, its text stays alone
def _with_parent(own: str, events: Sequence[Event], index: int, node: NodeId, value: float) -> str:
    if node == ():
        return own
    parent = node[:-1]
    is_max = _enter_of(events, index, parent).is_max
    earlier = _child_values(events, index, parent)
    player = _player(is_max)
    if not earlier:
        return own + " " + texts.NARRATE_PARENT_FIRST.format(parent=player, value=number_text(value))
    best = max(earlier) if is_max else min(earlier)
    goal = texts.GOAL_MAX if is_max else texts.GOAL_MIN
    if value == best:
        return own + " " + texts.NARRATE_PARENT_SAME.format(parent=player, goal=goal, value=number_text(value))
    # The parent says plainly whether the value is higher or lower, "better" would mean the opposite for MIN
    higher = value > best
    template = texts.NARRATE_PARENT_TAKES if higher == is_max else texts.NARRATE_PARENT_KEEPS
    compare = texts.COMPARE_MORE if higher else texts.COMPARE_LESS
    reaction = template.format(parent=player, goal=goal, value=number_text(value), compare=compare, old=number_text(best))
    return own + " " + reaction


# Values of the children of parent that finished before index
# The events are read backwards only until the search entered the parent, nothing before matters
def _child_values(events: Sequence[Event], index: int, parent: NodeId) -> list[float]:
    values = []
    for event in _backwards(events, index):
        if isinstance(event, Enter) and event.node == parent:
            break
        if isinstance(event, (Leaf, Exit)) and len(event.node) == len(parent) + 1 and event.node[:-1] == parent:
            values.append(event.value)
    return values


# The Enter event of a node, the last one before index
def _enter_of(events: Sequence[Event], index: int, node: NodeId) -> Enter:
    for event in _backwards(events, index):
        if isinstance(event, Enter) and event.node == node:
            return event
    raise ValueError(node)


# Alpha and beta of a node just before index, from its last bound update or from entering it
def _bounds_of(events: Sequence[Event], index: int, node: NodeId) -> tuple[float, float]:
    for event in _backwards(events, index):
        if isinstance(event, (BoundUpdate, Enter)) and event.node == node:
            return event.alpha, event.beta
    raise ValueError(node)


# Events before index from the newest to the oldest, without copying the list
def _backwards(events: Sequence[Event], index: int) -> Iterator[Event]:
    for i in range(index - 1, -1, -1):
        yield events[i]


# MAX or MIN as written in the texts
def _player(is_max: bool) -> str:
    return texts.PLAYER_MAX if is_max else texts.PLAYER_MIN
