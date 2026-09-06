"""Affiliation interval semantics: start-inclusive, end-exclusive (decision 1)."""

from datetime import date

import pytest

from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)
from app.shared.utils.datetime import utc_now


def _affiliation(
    valid_from: date = date(2026, 1, 1), valid_until: date | None = date(2026, 7, 1)
) -> ProviderAffiliationEntity:
    now = utc_now()
    return ProviderAffiliationEntity(
        id=ProviderAffiliationId("aff-1"),
        tenant_id=TenantId("t-1"),
        provider_id=ProviderId("prov-1"),
        organisation_id=ProviderOrganisationId("org-1"),
        valid_from=valid_from,
        valid_until=valid_until,
        created_at=now,
        updated_at=now,
    )


class TestCoverage:
    def test_start_is_inclusive(self):
        assert _affiliation().covers(date(2026, 1, 1))

    def test_end_is_exclusive(self):
        assert not _affiliation().covers(date(2026, 7, 1))

    def test_day_before_end_is_covered(self):
        assert _affiliation().covers(date(2026, 6, 30))

    def test_before_start_is_not_covered(self):
        assert not _affiliation().covers(date(2025, 12, 31))

    def test_open_ended_covers_any_later_day(self):
        assert _affiliation(valid_until=None).covers(date(2099, 1, 1))

    def test_open_ended_still_respects_start(self):
        assert not _affiliation(valid_until=None).covers(date(2025, 12, 31))


class TestOverlap:
    def test_adjacent_intervals_do_not_overlap(self):
        """One ending 2026-07-01 and the next starting 2026-07-01 are adjacent."""
        assert not _affiliation().overlaps(date(2026, 7, 1), date(2026, 12, 1))

    def test_interval_ending_exactly_at_start_does_not_overlap(self):
        assert not _affiliation().overlaps(date(2025, 6, 1), date(2026, 1, 1))

    def test_one_day_intrusion_overlaps(self):
        assert _affiliation().overlaps(date(2026, 6, 30), date(2026, 12, 1))

    def test_contained_interval_overlaps(self):
        assert _affiliation().overlaps(date(2026, 2, 1), date(2026, 3, 1))

    def test_containing_interval_overlaps(self):
        assert _affiliation().overlaps(date(2025, 1, 1), None)

    def test_open_ended_existing_overlaps_anything_after_start(self):
        assert _affiliation(valid_until=None).overlaps(date(2030, 1, 1), None)

    def test_open_ended_existing_does_not_overlap_earlier_closed_interval(self):
        assert not _affiliation(valid_until=None).overlaps(date(2025, 1, 1), date(2026, 1, 1))


class TestInvariants:
    def test_end_equal_to_start_is_rejected(self):
        with pytest.raises(DomainError):
            _affiliation(valid_until=date(2026, 1, 1))

    def test_end_before_start_is_rejected(self):
        with pytest.raises(DomainError):
            _affiliation(valid_until=date(2025, 1, 1))

    def test_change_end_requires_a_reason(self):
        with pytest.raises(DomainError):
            _affiliation().change_end(date(2026, 8, 1), UserId("u-1"), "  ")

    def test_change_end_emits_an_event_with_both_values(self):
        affiliation = _affiliation()
        affiliation.change_end(date(2026, 8, 1), UserId("u-1"), "Contract extended")
        assert len(affiliation.events) == 1
        event = affiliation.events[0]
        assert event.old_valid_until == date(2026, 7, 1)
        assert event.new_valid_until == date(2026, 8, 1)

    def test_unchanged_end_emits_nothing(self):
        affiliation = _affiliation()
        affiliation.change_end(date(2026, 7, 1), UserId("u-1"), "No change")
        assert affiliation.events == []

    def test_change_end_cannot_invert_the_interval(self):
        with pytest.raises(DomainError):
            _affiliation().change_end(date(2025, 1, 1), UserId("u-1"), "Typo")
