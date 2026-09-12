"""What each dashboard range preset resolves to.

The window arithmetic, kept away from the database. The year presets are the
reason this file exists: they are the only ones whose comparison window does
not sit immediately before them, and getting that wrong shows up as a
plausible but wrong percentage on the Sessions tile rather than as an error.
"""

from datetime import UTC, datetime

import pytest

from app.api.routes.dashboard import resolve_range
from app.domain.exceptions import ValidationException

NOW = datetime(2026, 9, 12, 14, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _freeze(monkeypatch):
    monkeypatch.setattr("app.api.routes.dashboard.utc_now", lambda: NOW)


class TestThisYear:
    def test_runs_from_january_to_now(self):
        window = resolve_range("this_year", None, None)
        assert window.start == datetime(2026, 1, 1, tzinfo=UTC)
        assert window.end == NOW

    def test_compares_against_the_same_stretch_of_last_year(self):
        """Not the months immediately before, which would end on 31 December."""
        window = resolve_range("this_year", None, None)
        assert window.prior_start == datetime(2025, 1, 1, tzinfo=UTC)
        assert window.prior_end == datetime(2025, 9, 12, 14, 30, tzinfo=UTC)

    def test_the_two_windows_are_the_same_length(self):
        window = resolve_range("this_year", None, None)
        assert window.end - window.start == window.prior_end - window.prior_start

    def test_buckets_by_month(self):
        assert resolve_range("this_year", None, None).granularity == "month"


class TestAnExplicitYear:
    def test_a_finished_year_runs_the_whole_year(self):
        window = resolve_range("year", None, None, year=2024)
        assert window.start == datetime(2024, 1, 1, tzinfo=UTC)
        assert window.end == datetime(2025, 1, 1, tzinfo=UTC)

    def test_a_finished_year_compares_against_the_whole_year_before(self):
        window = resolve_range("year", None, None, year=2024)
        assert window.prior_start == datetime(2023, 1, 1, tzinfo=UTC)
        assert window.prior_end == datetime(2024, 1, 1, tzinfo=UTC)

    def test_the_current_year_stops_at_now_rather_than_december(self):
        """A part-finished year compared with a full one would read as collapse."""
        window = resolve_range("year", None, None, year=2026)
        assert window.end == NOW
        assert window.prior_end == datetime(2025, 9, 12, 14, 30, tzinfo=UTC)

    def test_a_leap_year_does_not_drift_into_the_year_after_its_comparison(self):
        """2024 is 366 days. Shifting by duration rather than by the calendar
        put prior_end on 2 January 2024 and counted a day that belongs to the
        window being measured."""
        window = resolve_range("year", None, None, year=2024)
        assert window.prior_start == datetime(2023, 1, 1, tzinfo=UTC)
        assert window.prior_end == datetime(2024, 1, 1, tzinfo=UTC)
        assert window.prior_end == window.start

    def test_the_comparison_for_a_finished_year_is_exactly_the_year_before(self):
        for year in (2022, 2023, 2024, 2025):
            window = resolve_range("year", None, None, year=year)
            assert window.prior_start == datetime(year - 1, 1, 1, tzinfo=UTC), year
            assert window.prior_end == datetime(year, 1, 1, tzinfo=UTC), year

    def test_a_year_needs_to_be_given(self):
        with pytest.raises(ValidationException):
            resolve_range("year", None, None)

    def test_a_future_year_is_refused(self):
        with pytest.raises(ValidationException):
            resolve_range("year", None, None, year=2027)


class TestAllTime:
    def test_starts_at_the_first_delivery(self):
        window = resolve_range(
            "all_time", None, None, earliest=datetime(2021, 4, 3, 9, 0, tzinfo=UTC)
        )
        assert window.start == datetime(2021, 4, 3, tzinfo=UTC)
        assert window.end == NOW

    def test_offers_no_comparison_window(self):
        """There is nothing before all time; an empty window counts zero, and
        the frontend drops the delta rather than claiming infinite growth."""
        window = resolve_range(
            "all_time", None, None, earliest=datetime(2021, 4, 3, 9, 0, tzinfo=UTC)
        )
        assert window.prior_start == window.prior_end

    def test_a_tenant_that_has_delivered_nothing_gets_today(self):
        window = resolve_range("all_time", None, None, earliest=None)
        assert window.start == datetime(2026, 9, 12, tzinfo=UTC)

    def test_is_not_bound_by_the_custom_range_cap(self):
        """MAX_RANGE_DAYS guards a user-supplied window. This one is computed
        from the tenant's own first session, so eight years is legitimate."""
        window = resolve_range("all_time", None, None, earliest=datetime(2018, 1, 1, tzinfo=UTC))
        assert (window.end - window.start).days > 1095
        assert window.granularity == "month"


class TestTheOtherPresetsAreUnchanged:
    @pytest.mark.parametrize(
        ("preset", "expected_start"),
        [
            ("this_week", datetime(2026, 9, 7, tzinfo=UTC)),
            ("this_month", datetime(2026, 9, 1, tzinfo=UTC)),
        ],
    )
    def test_calendar_presets(self, preset, expected_start):
        assert resolve_range(preset, None, None).start == expected_start

    @pytest.mark.parametrize("preset", ["last_30d", "last_90d", "last_180d", "this_week"])
    def test_the_comparison_still_ends_where_the_window_begins(self, preset):
        window = resolve_range(preset, None, None)
        assert window.prior_end == window.start
