"""
State of the tree after applying a prefix of the event stream.

Rebuilt from scratch for every step.

It would make sense to add checkpoints only if this gets brutally slow. I hope it won't be necessary.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from math import inf

from minimax_sim.core.events import BoundUpdate, Enter, Event, Exit, Leaf, NodeId, Prune, ValueKind


# Where a node is in the search right now
#   UNVISITED  not reached yet
#   ACTIVE     the node the search is working on
#   ON_PATH    ancestor of the active node
#   DONE       finished, has its value
#   PRUNED     skipped by a prune
class Status(Enum):
    UNVISITED = "unvisited"
    ACTIVE = "active"
    ON_PATH = "on_path"
    DONE = "done"
    PRUNED = "pruned"


# What the GUI needs to know about one node
@dataclass(slots=True)
class NodeState:
    depth: int
    is_max: bool
    alpha: float = -inf
    beta: float = inf
    value: float | None = None
    kind: ValueKind | None = None
    status: Status = Status.UNVISITED


# The whole tree as it looks after a given step
#   active               node on top of the stack, None before the start and after the end
#   path                 from the root down to the active node
#   alpha, beta          bounds of the active node, for the number line
#   principal_variation  optimal line, only once the run has finished
@dataclass(slots=True)
class Snapshot:
    nodes: dict[NodeId, NodeState] = field(default_factory=dict)
    active: NodeId | None = None
    path: tuple[NodeId, ...] = ()
    alpha: float = -inf
    beta: float = inf
    last_event: Event | None = None
    principal_variation: tuple[NodeId, ...] = ()

    # Replay the events and build the state after the last one
    @classmethod
    def build(cls, events: Sequence[Event], finished: bool) -> "Snapshot":
        snap = cls()
        nodes = snap.nodes

        # Nodes entered and not left yet
        stack: list[NodeId] = []

        # Best move of every finished node, to build the optimal line
        best_moves: dict[NodeId, int | None] = {}

        for event in events:
            match event:
                case Enter(node=n, depth=d, is_max=m, alpha=a, beta=b):
                    nodes[n] = NodeState(d, m, a, b, status=Status.ACTIVE)
                    if stack:
                        nodes[stack[-1]].status = Status.ON_PATH
                    stack.append(n)
                case Leaf(node=n, value=v):
                    nodes[n].value, nodes[n].kind, nodes[n].status = v, ValueKind.EXACT, Status.DONE
                    stack.pop()
                case BoundUpdate(node=n, alpha=a, beta=b):
                    nodes[n].alpha, nodes[n].beta = a, b
                case Prune(node=n, skipped=skipped):
                    parent = nodes[n]
                    for i in skipped:
                        nodes[n + (i,)] = NodeState(parent.depth + 1, not parent.is_max, status=Status.PRUNED)
                case Exit(node=n, value=v, best_move=best, kind=k):
                    nodes[n].value, nodes[n].kind, nodes[n].status = v, k, Status.DONE
                    best_moves[n] = best
                    stack.pop()

            # After a leaf or an exit the parent becomes the active node again
            if stack:
                nodes[stack[-1]].status = Status.ACTIVE

        snap.last_event = events[-1] if events else None
        snap.path = tuple(stack)
        if stack:
            snap.active = stack[-1]
            snap.alpha, snap.beta = nodes[stack[-1]].alpha, nodes[stack[-1]].beta

        # Optimal line: follow best_move from the root down
        if finished and events:
            line = [()]
            while best_moves.get(line[-1]) is not None:
                line.append(line[-1] + (best_moves[line[-1]],))
            snap.principal_variation = tuple(line)
        return snap