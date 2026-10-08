"""
Lazy and cached reading of a search generator.
"""

from minimax_sim import config, texts
from minimax_sim.core.events import Event
from minimax_sim.core.search import Search, SearchResult


# Events of one search run, read from the generator only when someone needs them
#   events    everything read so far, kept for stepping back
#   finished  the generator will give nothing more, either it ended or hit the limit
#   result    set when the search ends normally
#   error     set when the event limit stops the search
class Trace:
    def __init__(self, gen: Search, max_events: int = config.MAX_EVENTS) -> None:
        self._gen = gen
        self._max = max_events
        self.events: list[Event] = []
        self.finished = False
        self.result: SearchResult | None = None
        self.error: str | None = None

    # Number of events read so far
    def __len__(self) -> int:
        return len(self.events)

    # trace[i] returns the i-th event read so far
    def __getitem__(self, i: int) -> Event:
        return self.events[i]

    # Read events up to index i, return whether event i exists
    def ensure(self, i: int) -> bool:
        while len(self.events) <= i and not self.finished:
            if len(self.events) >= self._max:
                self.finished = True
                self.error = texts.TRACE_LIMIT.format(limit=self._max)
                break
            try:
                self.events.append(next(self._gen))
            except StopIteration as stop:
                self.finished = True
                self.result = stop.value
        return i < len(self.events)

    # Read the whole run up to the event limit
    def ensure_all(self) -> None:
        self.ensure(self._max)