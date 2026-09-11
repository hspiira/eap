"""The tally has to survive SQLAlchemy running the query in a greenlet.

An async engine executes through `greenlet_spawn`, which copies the context
rather than sharing it. Holding a mutable tally in the context variable is what
makes the count the greenlet records readable by the caller, so these cover
that property directly rather than only the arithmetic around it.
"""

import asyncio
from contextlib import contextmanager

from sqlalchemy import create_engine, text

from app.core.query_metrics import Measured, QueryTally, install, measure_queries


@contextmanager
def _engine():
    install()
    engine = create_engine("sqlite://")
    try:
        yield engine
    finally:
        engine.dispose()


class TestTally:
    def test_records_each_query_and_its_time(self):
        tally = QueryTally()
        tally.record(0.010)
        tally.record(0.005)
        assert tally.queries == 2
        assert tally.ms == 15.0


class TestMeasured:
    def test_per_row_figures_divide_the_totals(self):
        measured = Measured()
        measured.elapsed = 2.0
        measured.tally.record(0.5)
        measured.tally.record(0.5)
        fields = measured.as_log_fields(4)
        assert fields["duration_ms"] == 2000.0
        assert fields["query_ms"] == 1000.0
        assert fields["queries"] == 2
        assert fields["ms_per_row"] == 500.0
        assert fields["queries_per_row"] == 0.5

    def test_an_empty_chunk_reports_totals_without_dividing_by_zero(self):
        measured = Measured()
        measured.elapsed = 0.1
        fields = measured.as_log_fields(0)
        assert fields["queries"] == 0
        assert "ms_per_row" not in fields


class TestMeasureQueries:
    def test_the_block_measures_its_own_wall_clock(self):
        with measure_queries() as measured:
            pass
        assert measured.duration_ms >= 0

    async def test_a_tally_set_before_a_task_is_still_written_to_inside_it(self):
        """Standing in for the greenlet: a copied context shares the same tally."""
        from app.core.query_metrics import _current

        async def inner():
            tally = _current.get()
            assert tally is not None
            tally.record(0.02)

        with measure_queries() as measured:
            await asyncio.create_task(inner())

        assert measured.tally.queries == 1
        assert measured.tally.ms == 20.0


class TestAgainstAnEngine:
    def test_it_counts_the_statements_the_block_actually_ran(self):
        with _engine() as engine, engine.connect() as conn:
            with measure_queries() as measured:
                for _ in range(3):
                    conn.execute(text("SELECT 1"))
            assert measured.tally.queries == 3

    def test_a_query_outside_the_block_is_not_counted(self):
        with _engine() as engine, engine.connect() as conn:
            with measure_queries() as measured:
                conn.execute(text("SELECT 1"))
            conn.execute(text("SELECT 1"))
            assert measured.tally.queries == 1

    def test_installing_twice_does_not_double_count(self):
        with _engine() as engine, engine.connect() as conn:
            install()
            with measure_queries() as measured:
                conn.execute(text("SELECT 1"))
            assert measured.tally.queries == 1

    def test_an_engine_created_after_install_is_measured_too(self):
        """Registered on the class, so nothing has to remember to opt an engine in."""
        install()
        engine = create_engine("sqlite://")
        try:
            with engine.connect() as conn, measure_queries() as measured:
                conn.execute(text("SELECT 1"))
            assert measured.tally.queries == 1
        finally:
            engine.dispose()
