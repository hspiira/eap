"""Staged import: provenance, separate outcomes, and replay keys."""

from datetime import UTC, date, datetime

import pytest

from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums.provider_network import (
    DeliveryContext,
    ImportBatchStatus,
    ImportRowOutcome,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    SessionImportBatchId,
    SessionImportRowId,
)

AT = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
ACTOR = UserId("u-1")
HASH = "sha256:abc123"


def _batch(**overrides) -> SessionImportBatchEntity:
    defaults = {
        "id": SessionImportBatchId("b-1"),
        "tenant_id": TenantId("t-1"),
        "source_system": "sessions-csv",
        "file_name": "sessions.csv",
        "file_hash": HASH,
        "row_count": 10,
        "staged_by": ACTOR,
        "created_at": AT,
        "updated_at": AT,
    }
    return SessionImportBatchEntity(**{**defaults, **overrides})


def _row(**overrides) -> SessionImportRowEntity:
    defaults = {
        "id": SessionImportRowId("r-1"),
        "batch_id": SessionImportBatchId("b-1"),
        "tenant_id": TenantId("t-1"),
        "row_number": 1,
        "source_record_key": None,
        "raw_practitioner_name": "Dr Alice Nakato",
        "session_date": date(2025, 4, 2),
        "outcome": ImportRowOutcome.ACCEPTED,
        "provider_id": ProviderId("prov-1"),
        "created_at": AT,
    }
    return SessionImportRowEntity(**{**defaults, **overrides})


class TestProvenance:
    def test_a_batch_requires_a_file_hash(self):
        with pytest.raises(DomainError):
            _batch(file_hash="")

    def test_a_batch_requires_a_source_system(self):
        with pytest.raises(DomainError):
            _batch(source_system="  ")

    def test_absent_source_key_field_means_file_hash_replay(self):
        assert _batch().uses_file_hash_replay_key is True

    def test_a_stable_source_key_field_is_recorded(self):
        assert _batch(source_record_key_field="ACTIVITY LOG ID").uses_file_hash_replay_key is False


class TestBatchLifecycle:
    def test_applying_records_actor_and_time(self):
        batch = _batch()
        batch.mark_applied(ACTOR, at=AT, accepted_count=7)
        assert batch.status is ImportBatchStatus.APPLIED
        assert (batch.applied_by, batch.applied_at) == (ACTOR, AT)

    def test_applying_emits_an_auditable_event_with_the_accepted_count(self):
        batch = _batch()
        batch.mark_applied(ACTOR, at=AT, accepted_count=7)
        assert [type(e).__name__ for e in batch.events] == ["SessionImportBatchApplied"]
        assert batch.events[0].accepted_count == 7

    def test_abandoning_emits_an_auditable_event_with_the_reason(self):
        batch = _batch()
        batch.abandon(ACTOR, "Wrong file", at=AT)
        assert [type(e).__name__ for e in batch.events] == ["SessionImportBatchAbandoned"]
        assert batch.events[0].reason == "Wrong file"

    def test_a_batch_cannot_be_applied_twice(self):
        """Replaying an applied batch must not silently reimport it."""
        batch = _batch()
        batch.mark_applied(ACTOR, at=AT, accepted_count=7)
        with pytest.raises(DomainError):
            batch.mark_applied(ACTOR, at=AT, accepted_count=7)

    def test_an_applied_batch_cannot_be_abandoned(self):
        batch = _batch()
        batch.mark_applied(ACTOR, at=AT, accepted_count=7)
        with pytest.raises(DomainError):
            batch.abandon(ACTOR, "Wrong file", at=AT)

    def test_abandoning_requires_a_reason(self):
        with pytest.raises(DomainError):
            _batch().abandon(ACTOR, " ", at=AT)


class TestRowOutcomes:
    def test_an_accepted_row_requires_a_practitioner(self):
        with pytest.raises(DomainError):
            _row(provider_id=None)

    def test_an_accepted_row_requires_a_session_date(self):
        with pytest.raises(DomainError):
            _row(session_date=None)

    @pytest.mark.parametrize(
        "outcome",
        [
            ImportRowOutcome.MISSING_PRACTITIONER,
            ImportRowOutcome.UNMAPPED_PRACTITIONER,
            ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
            ImportRowOutcome.CONFLICTING,
            ImportRowOutcome.REJECTED,
        ],
    )
    def test_every_review_outcome_must_record_a_reason(self, outcome):
        with pytest.raises(DomainError):
            _row(outcome=outcome, provider_id=None, reasons=())

    def test_the_three_practitioner_failures_stay_separate(self):
        """Missing, unmapped and ambiguous are distinct review outcomes."""
        outcomes = {
            _row(outcome=o, provider_id=None, raw_practitioner_name=None, reasons=("x",)).outcome
            for o in (
                ImportRowOutcome.MISSING_PRACTITIONER,
                ImportRowOutcome.UNMAPPED_PRACTITIONER,
                ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
            )
        }
        assert len(outcomes) == 3

    def test_only_accepted_rows_are_importable(self):
        assert _row().is_importable is True
        held = _row(
            outcome=ImportRowOutcome.UNMAPPED_PRACTITIONER, provider_id=None, reasons=("no match",)
        )
        assert held.is_importable is False
        assert held.needs_review is True


class TestDeliveryContext:
    def test_unknown_context_is_allowed_for_history(self):
        """Decision 2 permits unknown only on historical records."""
        assert _row(delivery_context=DeliveryContext.UNKNOWN).delivery_context is (
            DeliveryContext.UNKNOWN
        )

    def test_organisation_context_requires_an_affiliation(self):
        with pytest.raises(DomainError):
            _row(delivery_context=DeliveryContext.ORGANISATION)

    def test_direct_context_must_not_carry_an_affiliation(self):
        with pytest.raises(DomainError):
            _row(
                delivery_context=DeliveryContext.DIRECT,
                provider_affiliation_id=ProviderAffiliationId("aff-1"),
            )

    def test_unknown_context_must_not_carry_an_affiliation(self):
        with pytest.raises(DomainError):
            _row(
                delivery_context=DeliveryContext.UNKNOWN,
                provider_affiliation_id=ProviderAffiliationId("aff-1"),
            )

    def test_organisation_context_with_an_affiliation_is_accepted(self):
        row = _row(
            delivery_context=DeliveryContext.ORGANISATION,
            provider_affiliation_id=ProviderAffiliationId("aff-1"),
        )
        assert row.provider_affiliation_id == ProviderAffiliationId("aff-1")


class TestReplayKey:
    def test_file_hash_and_row_number_when_no_stable_key(self):
        assert _row().replay_key(HASH) == f"file:{HASH}:row:1"

    def test_a_stable_source_key_wins(self):
        assert _row(source_record_key="LOG-99").replay_key(HASH) == "key:LOG-99"

    def test_the_same_row_in_a_different_file_gets_a_different_key(self):
        """A changed file needs explicit reconciliation, not silent dedup."""
        assert _row().replay_key("sha256:other") != _row().replay_key(HASH)

    def test_row_numbers_are_one_based(self):
        with pytest.raises(DomainError):
            _row(row_number=0)
