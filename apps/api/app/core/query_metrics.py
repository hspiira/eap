"""Count SQL statements and the time spent in them, for a block of work.

An import writes one row per round trip, so knowing how long a chunk took says
nothing on its own about whether the time went on the database or on us. This
measures both, so the answer is read rather than assumed.

The context variable holds a mutable tally rather than a number, so the tally
SQLAlchemy's greenlet mutates is the same object the caller reads back when
the context is copied rather than shared.
"""

from __future__ import annotations

import contextvars
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from sqlalchemy import event
from sqlalchemy.engine import Engine


@dataclass
class QueryTally:
    """SQL statements executed while this tally was active, and their total time."""

    queries: int = 0
    seconds: float = 0.0

    def record(self, elapsed: float) -> None:
        self.queries += 1
        self.seconds += elapsed

    @property
    def ms(self) -> float:
        return round(self.seconds * 1000, 1)


@dataclass
class Measured:
    """Wall-clock and SQL cost of one measured block."""

    started: float = field(default_factory=time.perf_counter)
    tally: QueryTally = field(default_factory=QueryTally)
    elapsed: float = 0.0

    @property
    def duration_ms(self) -> float:
        return round(self.elapsed * 1000, 1)

    def per_row(self, rows: int) -> dict[str, float]:
        """The same figures divided by `rows`, or empty when nothing was written."""
        if rows <= 0:
            return {}
        return {
            "ms_per_row": round(self.duration_ms / rows, 2),
            "queries_per_row": round(self.tally.queries / rows, 2),
        }

    def as_log_fields(self, rows: int) -> dict[str, float]:
        return {
            "duration_ms": self.duration_ms,
            "query_ms": self.tally.ms,
            "queries": self.tally.queries,
            **self.per_row(rows),
        }


_current: contextvars.ContextVar[QueryTally | None] = contextvars.ContextVar(
    "current_query_tally", default=None
)


@contextmanager
def measure_queries():
    """Measure the wall-clock and SQL cost of the enclosed block."""
    measured = Measured()
    token = _current.set(measured.tally)
    try:
        yield measured
    finally:
        measured.elapsed = time.perf_counter() - measured.started
        _current.reset(token)


_installed = False


def install() -> None:
    """Count statements on every engine in the process. Idempotent.

    Registered against the `Engine` class rather than one instance, so a
    connection opened by a script or a test fixture is measured too. An engine
    that was missed would report zero queries rather than fail, which is the
    one way this instrument could mislead.
    """
    global _installed
    if _installed:
        return
    _installed = True

    @event.listens_for(Engine, "before_cursor_execute")
    def _before(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        conn.info["_query_started_at"] = time.perf_counter()

    @event.listens_for(Engine, "after_cursor_execute")
    def _after(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        tally = _current.get()
        started = conn.info.pop("_query_started_at", None)
        if tally is not None and started is not None:
            tally.record(time.perf_counter() - started)
