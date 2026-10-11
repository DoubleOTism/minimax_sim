"""
Counters of one whole search run, to compare how much work minimax and alpha-beta do.

A step is one event, so alpha-beta can take more steps than minimax on the same tree,
it adds bound updates and prunes. The counts of nodes and leaves show the real saving.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from minimax_sim.core.events import Enter, Event, Leaf, Prune


# Work done by one run
#   nodes    nodes the search entered, leaves included
#   leaves   leaves that were evaluated
#   pruned   moves skipped by pruning, each one is a whole subtree left out
#   steps    events of the run
@dataclass(frozen=True, slots=True)
class Stats:
    nodes: int
    leaves: int
    pruned: int
    steps: int


# Count the work in the events of a run
def count(events: Iterable[Event]) -> Stats:
    nodes = leaves = pruned = steps = 0
    for event in events:
        steps += 1
        match event:
            case Enter():
                nodes += 1
            case Leaf():
                leaves += 1
            case Prune(skipped=skipped):
                pruned += len(skipped)
    return Stats(nodes, leaves, pruned, steps)
