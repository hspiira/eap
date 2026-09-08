"""One report context, built once and applied by every section.

Sections used to parse the run parameters individually, which is how a client
filter reached one section and not the next (MODULES_REPAIR_PLAN REP-02).
"""

from datetime import date, datetime

import pytest

from app.domain.exceptions import DomainError
from app.domain.services.report_context import ReportContext, build_report_context


def _context(**params) -> ReportContext:
    return build_report_context(tenant_id="t-1", parameters=params)


class TestParameters:
    def test_an_unsupported_parameter_is_rejected_not_ignored(self):
        with pytest.raises(DomainError, match="clientId"):
            _context(clientId="c-1")

    def test_the_supported_parameters_are_normalized(self):
        context = _context(client_id="c-1", **{"from": "2025-06-01", "to": "2026-05-31"})
        assert context.client_id == "c-1"
        assert context.date_from == date(2025, 6, 1)
        assert context.date_to == date(2026, 5, 31)

    def test_a_timestamp_parameter_is_read_as_its_calendar_day(self):
        assert _context(**{"to": "2026-01-31T14:30:00"}).date_to == date(2026, 1, 31)

    def test_a_reversed_period_is_rejected(self):
        with pytest.raises(DomainError, match="on or after"):
            _context(**{"from": "2026-05-31", "to": "2025-06-01"})

    def test_an_unparseable_date_is_rejected(self):
        with pytest.raises(DomainError, match="not a date"):
            _context(**{"from": "last June"})

    def test_an_unknown_timezone_is_rejected(self):
        with pytest.raises(DomainError, match="Unknown report timezone"):
            _context(timezone="Mars/Olympus")

    def test_the_default_timezone_is_utc(self):
        assert _context().timezone == "UTC"


class TestPeriodBounds:
    def test_the_end_bound_is_the_day_after_the_inclusive_end_date(self):
        """A record on the afternoon of the last day is inside the window."""
        context = _context(**{"to": "2026-01-31"})
        assert context.end_before() == datetime.fromisoformat("2026-02-01T00:00:00+00:00")

    def test_bounds_follow_the_report_timezone(self):
        context = _context(**{"from": "2026-01-01", "to": "2026-01-31"}, timezone="Africa/Kampala")
        assert context.start_at().utcoffset().total_seconds() == 3 * 3600
        assert context.start_at().isoformat() == "2026-01-01T00:00:00+03:00"
        assert context.end_before().isoformat() == "2026-02-01T00:00:00+03:00"

    def test_an_open_period_has_no_bounds(self):
        context = _context()
        assert context.start_at() is None
        assert context.end_before() is None


class TestScope:
    def test_the_scope_reports_what_the_section_applied(self):
        scope = _context(client_id="c-1", **{"to": "2026-01-31"}).scope()
        assert scope["client_id"] == "c-1"
        assert scope["to"] == "2026-01-31"
        assert scope["ignored_parameters"] == []

    def test_a_parameter_a_section_cannot_use_is_named(self):
        scope = _context(campaign_id="cc-1").scope(ignored=["campaign_id"])
        assert scope["ignored_parameters"] == ["campaign_id"]
