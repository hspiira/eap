"""Staging outcomes: separate name failures, no future bookings, replay safety."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.services.provider_alias_reconciliation import (
    NameOutcome,
    NameResolution,
)
from app.application.services.session_import_staging import (
    SessionImportStagingService,
    SourceRow,
)
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.enums.provider_network import DeliveryContext, ImportRowOutcome
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
    SessionImportBatchId,
)

TENANT = TenantId("t-1")
SOURCE = "sessions-csv"
HASH = "sha256:abc"
NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
PROV = ProviderId("prov-1")


def _service(*, resolution=None, affiliation=None, existing_row=None):
    aliases = AsyncMock()
    aliases.resolve.return_value = resolution or NameResolution(
        outcome=NameOutcome.RESOLVED, provider_id=PROV, normalized_value="alice nakato"
    )
    affiliations = AsyncMock()
    affiliations.get_valid_affiliation.return_value = affiliation
    imports = AsyncMock()
    imports.find_row_by_replay_key.return_value = existing_row
    return SessionImportStagingService(aliases, affiliations, imports), imports


def _row(**overrides) -> SourceRow:
    defaults = {
        "row_number": 1,
        "raw_practitioner_name": "Dr Alice Nakato",
        "session_date": date(2025, 4, 2),
    }
    return SourceRow(**{**defaults, **overrides})


async def _stage(service, row):
    return await service.stage_row(TENANT, SOURCE, HASH, row, now=NOW)


class TestHistoricalAcceptance:
    async def test_a_past_session_for_a_resolved_practitioner_is_accepted(self):
        """Eligibility today is irrelevant: the delivery already happened."""
        service, _ = _service()
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.provider_id == PROV

    async def test_no_supplier_evidence_stays_unknown_not_direct(self):
        """Decision 2 forbids reading an empty organisation column as direct."""
        service, _ = _service()
        staged = await _stage(service, _row())
        assert staged.delivery_context is DeliveryContext.UNKNOWN
        assert staged.provider_affiliation_id is None

    async def test_a_future_dated_row_is_rejected(self):
        service, _ = _service()
        staged = await _stage(service, _row(session_date=date(2027, 1, 1)))
        assert staged.outcome is ImportRowOutcome.REJECTED
        assert "cannot create a booking" in staged.reasons[0]

    async def test_the_import_day_itself_is_accepted(self):
        """Boundary: the day the import runs is history, not a future booking."""
        service, _ = _service()
        staged = await _stage(service, _row(session_date=date(2026, 9, 6)))
        assert staged.outcome is ImportRowOutcome.ACCEPTED

    async def test_a_row_with_no_date_is_rejected(self):
        service, _ = _service()
        staged = await _stage(service, _row(session_date=None))
        assert staged.outcome is ImportRowOutcome.REJECTED
        assert staged.reasons


class TestNameOutcomesStaySeparate:
    @pytest.mark.parametrize(
        "name_outcome,expected",
        [
            (NameOutcome.MISSING, ImportRowOutcome.MISSING_PRACTITIONER),
            (NameOutcome.UNMAPPED, ImportRowOutcome.UNMAPPED_PRACTITIONER),
            (NameOutcome.AMBIGUOUS, ImportRowOutcome.AMBIGUOUS_PRACTITIONER),
            (NameOutcome.REJECTED, ImportRowOutcome.REJECTED),
        ],
    )
    async def test_each_name_failure_maps_to_its_own_outcome(self, name_outcome, expected):
        service, _ = _service(resolution=NameResolution(outcome=name_outcome, reasons=("why",)))
        staged = await _stage(service, _row())
        assert staged.outcome is expected
        assert staged.provider_id is None

    async def test_a_held_row_carries_the_reason(self):
        service, _ = _service(
            resolution=NameResolution(
                outcome=NameOutcome.AMBIGUOUS, reasons=("matches prov-1, prov-2",)
            )
        )
        staged = await _stage(service, _row())
        assert staged.reasons == ("matches prov-1, prov-2",)

    async def test_no_practitioner_is_invented_for_an_unmapped_name(self):
        service, _ = _service(
            resolution=NameResolution(outcome=NameOutcome.UNMAPPED, reasons=("no mapping",))
        )
        staged = await _stage(service, _row())
        assert staged.provider_id is None
        assert staged.outcome is ImportRowOutcome.UNMAPPED_PRACTITIONER


class TestOrganisationContext:
    def _affiliation(self):
        return ProviderAffiliationEntity(
            id=ProviderAffiliationId("aff-1"),
            tenant_id=TENANT,
            provider_id=PROV,
            organisation_id=ProviderOrganisationId("org-1"),
            valid_from=date(2025, 1, 1),
            valid_until=None,
            created_at=NOW,
            updated_at=NOW,
        )

    async def test_a_valid_affiliation_gives_organisation_context(self):
        service, _ = _service(affiliation=self._affiliation())
        staged = await _stage(service, _row(organisation_affiliation_id="aff-1"))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.delivery_context is DeliveryContext.ORGANISATION
        assert staged.provider_affiliation_id == ProviderAffiliationId("aff-1")

    async def test_an_affiliation_invalid_at_the_session_date_conflicts(self):
        """Not accepted as unknown: the source asserted a firm that does not hold."""
        service, _ = _service(affiliation=None)
        staged = await _stage(service, _row(organisation_affiliation_id="aff-1"))
        assert staged.outcome is ImportRowOutcome.CONFLICTING
        assert "not valid for this practitioner" in staged.reasons[0]

    async def test_the_affiliation_is_checked_at_the_session_date_not_today(self):
        service, _ = _service(affiliation=self._affiliation())
        affiliations = service._affiliations
        await _stage(
            service, _row(session_date=date(2025, 4, 2), organisation_affiliation_id="aff-1")
        )
        _, kwargs = affiliations.get_valid_affiliation.call_args
        assert kwargs["at"].date() == date(2025, 4, 2)


class TestReplay:
    async def test_a_row_already_staged_is_a_duplicate(self):
        existing = AsyncMock()
        existing.row_number = 7
        existing.batch_id = SessionImportBatchId("b-old")
        service, _ = _service(existing_row=existing)
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.DUPLICATE
        assert "batch b-old" in staged.reasons[0]

    async def test_the_replay_key_uses_file_hash_and_row_when_no_source_key(self):
        service, _ = _service()
        staged = await _stage(service, _row(row_number=42))
        assert staged.replay_key == f"file:{HASH}:row:42"

    async def test_a_stable_source_key_takes_precedence(self):
        service, _ = _service()
        staged = await _stage(service, _row(source_record_key="LOG-9"))
        assert staged.replay_key == "key:LOG-9"

    async def test_duplicate_detection_happens_before_any_resolution(self):
        """A replay must not re-run reconciliation or re-read affiliations."""
        existing = AsyncMock()
        existing.row_number = 1
        existing.batch_id = SessionImportBatchId("b-old")
        service, _ = _service(existing_row=existing)
        await _stage(service, _row())
        service._aliases.resolve.assert_not_awaited()
        service._affiliations.get_valid_affiliation.assert_not_awaited()
