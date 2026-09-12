"""The assumed length of a booking, and what counts as a clash.

A booking says when it starts and nothing about how long it runs, so the
length comes from the service. These pin the assumption, because it is what
every conflict decision rests on.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.services.session_scheduling import (
    DEFAULT_SESSION_MINUTES,
    booking_end,
    booking_minutes,
    spans_overlap,
)

AT = datetime(2026, 4, 3, 10, 0, tzinfo=UTC)


class TestBookingMinutes:
    def test_the_service_length_is_used_when_it_has_one(self):
        assert booking_minutes(90) == 90

    @pytest.mark.parametrize("absent", [None, 0, -30])
    def test_a_missing_or_nonsense_length_falls_back_to_the_nominal_hour(self, absent):
        assert booking_minutes(absent) == DEFAULT_SESSION_MINUTES

    def test_the_fallback_is_an_hour(self):
        """Named because the API reports it and a scheduler has to trust it."""
        assert DEFAULT_SESSION_MINUTES == 60


class TestBookingEnd:
    def test_a_service_with_a_length_ends_after_it(self):
        assert booking_end(AT, 90) == datetime(2026, 4, 3, 11, 30, tzinfo=UTC)

    def test_a_service_without_one_ends_after_the_nominal_hour(self):
        assert booking_end(AT, None) == datetime(2026, 4, 3, 11, 0, tzinfo=UTC)


class TestSpansOverlap:
    def _span(self, start_hour: float, minutes: int = 60):
        start = AT.replace(hour=int(start_hour), minute=int((start_hour % 1) * 60))
        return start, start + timedelta(minutes=minutes)

    def test_two_bookings_at_the_same_time_clash(self):
        a, b = self._span(10), self._span(10)
        assert spans_overlap(*a, *b)

    def test_a_partial_overlap_clashes(self):
        a, b = self._span(10), self._span(10.5)
        assert spans_overlap(*a, *b)

    def test_back_to_back_bookings_do_not_clash(self):
        """The half-open boundary: 10-11 and 11-12 are a normal working day."""
        a, b = self._span(10), self._span(11)
        assert not spans_overlap(*a, *b)

    def test_separate_bookings_do_not_clash(self):
        a, b = self._span(10), self._span(14)
        assert not spans_overlap(*a, *b)

    def test_a_booking_wholly_inside_another_clashes(self):
        a = self._span(10, minutes=180)
        b = self._span(11, minutes=30)
        assert spans_overlap(*a, *b)

    def test_the_check_does_not_depend_on_which_span_comes_first(self):
        a, b = self._span(10), self._span(10.5)
        assert spans_overlap(*a, *b) == spans_overlap(*b, *a)
