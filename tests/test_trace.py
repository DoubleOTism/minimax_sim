"""
Tests for lazy reading of a search run.
"""

from minimax_sim import texts
from minimax_sim.core.events import Enter
from minimax_sim.core.search import alphabeta, minimax
from minimax_sim.session.trace import Trace


# Nothing is read until asked, then exactly as much as needed
def test_lazy_reading(rosen):
    trace = Trace(minimax(rosen, rosen.initial_state()))
    assert len(trace) == 0 and not trace.finished
    assert trace.ensure(0)
    assert len(trace) == 1 and isinstance(trace[0], Enter)
    assert trace.ensure(4)
    assert len(trace) == 5
    assert not trace.finished
    assert trace.result is None


# Reading past the end finishes the run and keeps its result
def test_result_and_finished(rosen):
    trace = Trace(alphabeta(rosen, rosen.initial_state()))
    assert not trace.ensure(10_000)
    assert trace.finished
    assert trace.result.value == 3 and trace.result.best_move == 0
    assert trace.error is None


# The event limit stops the run with an error instead of a result
def test_event_limit(rosen):
    trace = Trace(minimax(rosen, rosen.initial_state()), max_events=5)
    assert not trace.ensure(100)
    assert len(trace) == 5
    assert trace.finished and trace.result is None
    assert trace.error == texts.TRACE_LIMIT.format(limit=5)
