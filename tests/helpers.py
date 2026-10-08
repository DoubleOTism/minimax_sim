"""
Shared helpers for the search tests.
"""

from minimax_sim.core.events import Enter, Event, Exit, Leaf, Prune
from minimax_sim.core.search import SearchResult


# Runs a search to the end, returns all its events and the final result
def run(gen) -> tuple[list[Event], SearchResult]:
    events = []
    while True:
        try:
            events.append(next(gen))
        except StopIteration as stop:
            return events, stop.value


# Values of the leaves in the order they were evaluated
def leaves(events):
    return [e.value for e in events if isinstance(e, Leaf)]


# Number of nodes the search entered
def visited(events):
    return sum(isinstance(e, Enter) for e in events)


# Number of prunes
def prunes(events):
    return sum(isinstance(e, Prune) for e in events)


# Optimal line: follows best_move from the root down to a leaf
def principal_variation(events):
    exits = {e.node: e for e in events if isinstance(e, Exit)}
    path = ()
    while path in exits and exits[path].best_move is not None:
        path = path + (exits[path].best_move,)
    return path
