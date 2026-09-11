"""Mapper-level evidence that OutreachRecord.notes/triage_responses/
triage_scores are encrypted at rest, matching the sibling clinical fields."""

from datetime import UTC, datetime

import pytest

from app.core.encryption import EncryptionError, KeyProvider, set_key_provider
from app.domain.entities.outreach_record import OutreachRecord
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    EligibleMemberId,
    OutreachRecordId,
    TenantId,
)
from app.infrastructure.mappers.care_callback_mapper import OutreachRecordMapper
from app.infrastructure.models.care_callback_model import OutreachRecordModel


class _FixedKeyProvider(KeyProvider):
    def __init__(self, raw: bytes):
        self._raw = raw

    def get_kek(self) -> bytes:
        return self._raw


@pytest.fixture(autouse=True)
def isolate_provider():
    set_key_provider(_FixedKeyProvider(b"x" * 32))
    yield
    set_key_provider(_FixedKeyProvider(b"x" * 32))


def _make_outreach(
    tenant: str,
    *,
    notes: str | None = None,
    triage_responses: dict | None = None,
    triage_scores: dict | None = None,
) -> OutreachRecord:
    now = datetime.now(UTC)
    return OutreachRecord(
        id=OutreachRecordId("or-1"),
        tenant_id=TenantId(tenant),
        campaign_id=CareCallbackCampaignId("camp-1"),
        member_id=EligibleMemberId("member-1"),
        created_at=now,
        updated_at=now,
        notes=notes,
        triage_responses=triage_responses,
        triage_scores=triage_scores,
    )


class TestOutreachRecordEncryptionWiring:
    def test_to_model_persists_ciphertext_not_plaintext(self):
        entity = _make_outreach(
            "t-1",
            notes="Discloses ongoing self-harm ideation.",
            triage_responses={"q1": "yes"},
            triage_scores={"phq9": 21},
        )

        model = OutreachRecordMapper.to_model(entity)

        assert model.notes is not None
        assert "self-harm" not in model.notes
        assert model.triage_responses is not None
        assert "q1" not in model.triage_responses
        assert model.triage_scores is not None
        assert "phq9" not in model.triage_scores

    def test_round_trip_preserves_plaintext(self):
        entity = _make_outreach(
            "t-1",
            notes="Sensitive outreach note",
            triage_responses={"q1": "yes"},
            triage_scores={"phq9": 12},
        )
        model = OutreachRecordMapper.to_model(entity)

        rehydrated = OutreachRecordMapper.to_entity(model)
        assert rehydrated.notes == "Sensitive outreach note"
        assert rehydrated.triage_responses == {"q1": "yes"}
        assert rehydrated.triage_scores == {"phq9": 12}

    def test_none_remains_none_through_mapper(self):
        entity = _make_outreach("t-1")
        model = OutreachRecordMapper.to_model(entity)
        assert model.notes is None
        assert model.triage_responses is None
        assert model.triage_scores is None
        rehydrated = OutreachRecordMapper.to_entity(model)
        assert rehydrated.notes is None
        assert rehydrated.triage_responses is None
        assert rehydrated.triage_scores is None

    def test_ciphertext_is_tenant_bound(self):
        entity_a = _make_outreach("t-A", notes="shared text")
        entity_b = _make_outreach("t-B", notes="shared text")
        model_a = OutreachRecordMapper.to_model(entity_a)
        model_b = OutreachRecordMapper.to_model(entity_b)
        assert model_a.notes != model_b.notes

        forged = OutreachRecordModel(
            id=model_a.id,
            tenant_id="t-B",
            campaign_id=model_a.campaign_id,
            member_id=model_a.member_id,
            status=model_a.status,
            contact_attempts=model_a.contact_attempts,
            notes=model_a.notes,
            crisis_flag=model_a.crisis_flag,
            created_at=model_a.created_at,
            updated_at=model_a.updated_at,
        )
        with pytest.raises(EncryptionError):
            OutreachRecordMapper.to_entity(forged)
