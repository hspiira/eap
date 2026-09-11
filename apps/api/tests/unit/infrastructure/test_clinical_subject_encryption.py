"""Mapper-level evidence that ClinicalSubject.notes_for_continuity is
encrypted at rest, matching the sibling clinical/PII fields."""

from datetime import UTC, datetime

import pytest

from app.core.encryption import EncryptionError, KeyProvider, set_key_provider
from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.value_objects.core import ClinicalSubjectId, TenantId
from app.infrastructure.mappers.eligible_member_mapper import ClinicalSubjectMapper
from app.infrastructure.models.eligible_member_model import ClinicalSubjectModel


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


def _make_subject(tenant: str, *, notes_for_continuity: str | None = None) -> ClinicalSubject:
    now = datetime.now(UTC)
    return ClinicalSubject(
        id=ClinicalSubjectId("subj-1"),
        tenant_id=TenantId(tenant),
        pseudonym="PSEUDO-1",
        created_at=now,
        updated_at=now,
        notes_for_continuity=notes_for_continuity,
    )


class TestClinicalSubjectEncryptionWiring:
    def test_to_model_persists_ciphertext_not_plaintext(self):
        plaintext = "Prefers a female counsellor; history of workplace harassment."
        entity = _make_subject("t-1", notes_for_continuity=plaintext)

        model = ClinicalSubjectMapper.to_model(entity)

        assert model.notes_for_continuity is not None
        assert plaintext not in model.notes_for_continuity

    def test_round_trip_preserves_plaintext(self):
        entity = _make_subject("t-1", notes_for_continuity="Prefers morning sessions")
        model = ClinicalSubjectMapper.to_model(entity)

        rehydrated = ClinicalSubjectMapper.to_entity(model)
        assert rehydrated.notes_for_continuity == "Prefers morning sessions"

    def test_none_remains_none_through_mapper(self):
        entity = _make_subject("t-1")
        model = ClinicalSubjectMapper.to_model(entity)
        assert model.notes_for_continuity is None
        rehydrated = ClinicalSubjectMapper.to_entity(model)
        assert rehydrated.notes_for_continuity is None

    def test_ciphertext_is_tenant_bound(self):
        entity_a = _make_subject("t-A", notes_for_continuity="shared text")
        entity_b = _make_subject("t-B", notes_for_continuity="shared text")
        model_a = ClinicalSubjectMapper.to_model(entity_a)
        model_b = ClinicalSubjectMapper.to_model(entity_b)
        assert model_a.notes_for_continuity != model_b.notes_for_continuity

        forged = ClinicalSubjectModel(
            id=model_a.id,
            tenant_id="t-B",
            pseudonym=model_a.pseudonym,
            notes_for_continuity=model_a.notes_for_continuity,
            created_at=model_a.created_at,
            updated_at=model_a.updated_at,
        )
        with pytest.raises(EncryptionError):
            ClinicalSubjectMapper.to_entity(forged)
