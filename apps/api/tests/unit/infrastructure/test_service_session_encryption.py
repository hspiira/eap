"""Mapper-level evidence that service_session notes/feedback are encrypted at rest."""

from datetime import UTC, datetime

import pytest

from app.core.encryption import EncryptionError, KeyProvider, set_key_provider
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionStatus
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    PersonId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.infrastructure.mappers.service_session_mapper import ServiceSessionMapper


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


def _make_entity(tenant: str, notes: str | None, feedback: str | None) -> ServiceSessionEntity:
    now = datetime.now(UTC)
    return ServiceSessionEntity(
        id=SessionId("ses-1"),
        tenant_id=TenantId(tenant),
        service_id=ServiceId("svc-1"),
        provider_id=PersonId("prov-1"),
        client_id=ClientId("cli-1"),
        member_id=EligibleMemberId("per-1"),
        scheduled_at=now,
        status=SessionStatus.SCHEDULED,
        created_at=now,
        updated_at=now,
        reschedule_count=0,
        notes=notes,
        feedback=feedback,
    )


class TestServiceSessionEncryptionWiring:
    def test_to_model_persists_ciphertext_not_plaintext(self):
        plaintext_notes = "Patient reports persistent insomnia and intrusive thoughts."
        plaintext_feedback = "Helpful session; will continue."
        entity = _make_entity("t-1", plaintext_notes, plaintext_feedback)

        model = ServiceSessionMapper.to_model(entity)

        assert model.notes is not None
        assert model.feedback is not None
        assert model.notes != plaintext_notes
        assert model.feedback != plaintext_feedback
        assert plaintext_notes not in (model.notes or "")
        assert plaintext_feedback not in (model.feedback or "")

    def test_round_trip_preserves_plaintext(self):
        entity = _make_entity("t-1", "session note", "client feedback")
        model = ServiceSessionMapper.to_model(entity)

        # Cross-aggregate copy: the model carries ciphertext; mapping back
        # decrypts using the model's own tenant_id.
        rehydrated = ServiceSessionMapper.to_entity(model)
        assert rehydrated.notes == "session note"
        assert rehydrated.feedback == "client feedback"

    def test_none_remains_none_through_mapper(self):
        entity = _make_entity("t-1", None, None)
        model = ServiceSessionMapper.to_model(entity)
        assert model.notes is None
        assert model.feedback is None
        rehydrated = ServiceSessionMapper.to_entity(model)
        assert rehydrated.notes is None
        assert rehydrated.feedback is None

    def test_ciphertext_is_tenant_bound(self):
        entity_a = _make_entity("t-A", "shared text", None)
        entity_b = _make_entity("t-B", "shared text", None)
        model_a = ServiceSessionMapper.to_model(entity_a)
        model_b = ServiceSessionMapper.to_model(entity_b)
        assert model_a.notes != model_b.notes

        # If tenant is forged on the model, decryption must fail.
        forged = type(model_a)(
            id=model_a.id,
            tenant_id="t-B",
            service_id=model_a.service_id,
            provider_id=model_a.provider_id,
            client_id=model_a.client_id,
            attendance=model_a.attendance,
            member_id=model_a.member_id,
            scheduled_at=model_a.scheduled_at,
            status=model_a.status,
            reschedule_count=model_a.reschedule_count,
            notes=model_a.notes,
        )
        with pytest.raises(EncryptionError):
            ServiceSessionMapper.to_entity(forged)
