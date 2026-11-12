"""
The API the GUI actually talks to.

One instance per tab.
"""

from enum import Enum

from minimax_sim import config, texts
from minimax_sim.core.events import NodeId
from minimax_sim.core.game import Game
from minimax_sim.core.search import Search, alphabeta, minimax
from minimax_sim.session.layout import Layout, layout
from minimax_sim.session.narration import explain
from minimax_sim.session.snapshot import Snapshot
from minimax_sim.session.stats import Stats, count
from minimax_sim.session.trace import Trace


# Which algorithm the tab is stepping through
class Algorithm(Enum):
    MINIMAX = "minimax"
    ALPHABETA = "alphabeta"


# Holds one loaded position, one search run over it and the current step
#   position  index of the last applied event, -1 means before the first one
class Controller:
    def __init__(self) -> None:
        self.game: Game | None = None
        self.state = None
        self.depth_limit: int | None = None
        self.algorithm = Algorithm.MINIMAX
        self.prune_on_equal = True
        self.right_to_left = False
        self.position = -1
        self._trace: Trace | None = None
        self._layout: Layout | None = None
        self._cached_snapshot: tuple[tuple[int, bool], Snapshot] | None = None
        self._cached_stats: tuple[tuple[bool, bool], dict[Algorithm, Stats | None]] | None = None

    #####
    # setup
    #####

    # New position: lay out its tree and start a new run
    def load(self, game: Game, state, depth_limit: int | None = None) -> None:
        self.game, self.state, self.depth_limit = game, state, depth_limit
        self._layout = layout(game, state, depth_limit)
        self._cached_stats = None
        self._restart()

    # Switch between minimax and alpha-beta, the run starts again
    def set_algorithm(self, algorithm: Algorithm) -> None:
        self.algorithm = algorithm
        self._restart()

    # Switch between pruning on alpha >= beta and alpha > beta, the run starts again
    def set_prune_on_equal(self, prune_on_equal: bool) -> None:
        self.prune_on_equal = prune_on_equal
        self._restart()

    # Switch between trying the moves left to right and right to left, the run starts again
    def set_right_to_left(self, right_to_left: bool) -> None:
        self.right_to_left = right_to_left
        self._restart()

    # Fresh search of the loaded position with the given algorithm, the current pruning rule and move order
    def _new_search(self, algorithm: Algorithm) -> Search:
        if algorithm is Algorithm.MINIMAX:
            return minimax(self.game, self.state, self.depth_limit, right_to_left=self.right_to_left)
        return alphabeta(
            self.game,
            self.state,
            self.depth_limit,
            prune_on_equal=self.prune_on_equal,
            right_to_left=self.right_to_left,
        )

    # Throw the old run away and go back before the first step
    def _restart(self) -> None:
        self._trace = Trace(self._new_search(self.algorithm))
        self._cached_snapshot = None
        self.position = -1

    #####
    # stepping
    #####

    # Whether there is a next event (reads it if needed)
    @property
    def can_step_forward(self) -> bool:
        return self._trace.ensure(self.position + 1)

    # Whether there is a previous step
    @property
    def can_step_back(self) -> bool:
        return self.position >= 0

    # Jump to step i, clamped to what exists
    def seek(self, i: int) -> None:
        self._trace.ensure(i + 1)
        self.position = max(-1, min(i, len(self._trace) - 1))

    def step_forward(self) -> None:
        self.seek(self.position + 1)

    def step_back(self) -> None:
        self.seek(self.position - 1)

    def to_start(self) -> None:
        self.seek(-1)

    # Read the whole run and jump to its last step
    def to_end(self) -> None:
        self._trace.ensure_all()
        self.seek(len(self._trace) - 1)

    #####
    # reading
    #####

    # Total number of steps, known only once the run has been read to the end
    @property
    def total_steps(self) -> int | None:
        return len(self._trace) if self._trace.finished else None

    # State of the tree at the current step, the last one is cached
    # The cache key includes "finished", the last step looks different once the run is
    # known to be over (the optimal line appears), even though the position is the same
    def snapshot(self) -> Snapshot:
        finished = self._trace.finished and self.position == len(self._trace) - 1
        key = (self.position, finished)
        if self._cached_snapshot is None or self._cached_snapshot[0] != key:
            events = self._trace.events[: self.position + 1]
            self._cached_snapshot = (key, Snapshot.build(events, finished))
        return self._cached_snapshot[1]

    # What happened in the current step, in plain words
    def explanation(self) -> str:
        if self.position < 0:
            return texts.STEP_NOT_STARTED
        show_bounds = self.algorithm is Algorithm.ALPHABETA
        return explain(self._trace.events, self.position, self._move_label, show_bounds)

    # Name of the move that leads to a node, empty when the game does not name its moves
    def _move_label(self, node: NodeId) -> str:
        return self.game.move_label(self.node_move(node))

    # Game state in a node, the moves on its path played from the loaded position
    def node_state(self, node: NodeId):
        state = self.state
        for index in node:
            state = self.game.apply(state, self.game.moves(state)[index])
        return state

    # Move that led to a node, None for the root
    def node_move(self, node: NodeId):
        if not node:
            return None
        return self.game.moves(self.node_state(node[:-1]))[node[-1]]

    # Node positions, None if the tree is too big to draw
    def layout(self) -> Layout | None:
        return self._layout

    # Message for the GUI when the tree is too big, None if it can be drawn
    @property
    def layout_error(self) -> str | None:
        if self._layout is not None:
            return None
        return texts.TREE_TOO_BIG.format(limit=config.MAX_DRAWN_NODES)

    # Counters of whole runs of both algorithms, None for a run stopped by the event limit
    # Computed once per position, pruning rule and move order, the stepping does not change them
    def stats(self) -> dict[Algorithm, Stats | None]:
        key = (self.prune_on_equal, self.right_to_left)
        if self._cached_stats is None or self._cached_stats[0] != key:
            stats = {algorithm: self._run_stats(algorithm) for algorithm in Algorithm}
            self._cached_stats = (key, stats)
        return self._cached_stats[1]

    # Run one algorithm to the end and count its work
    def _run_stats(self, algorithm: Algorithm) -> Stats | None:
        trace = Trace(self._new_search(algorithm))
        trace.ensure_all()
        if trace.error is not None:
            return None
        return count(trace.events)
