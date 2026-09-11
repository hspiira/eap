"""Mapper-level evidence that a clinical note's body and amendments are
encrypted at rest, matching the sibling ServiceSession/EligibleMember fields."""

from datetime import UTC, datetime

import pytest

from app.core.encryption import EncryptionError, KeyProvider, set_key_provider
from app.domain.entities.clinical_note import ClinicalNote, NoteAmendment
from app.domain.enums import ClinicalNoteType
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    ClinicalSubjectId,
    NoteAmendmentId,
    TenantId,
    UserId,
)
from app.infrastructure.mappers.clinical_note_mapper import ClinicalNoteMapper
from app.infrastructure.models.clinical_note_model import ClinicalNoteModel


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


def _make_entity(
    tenant: str,
    *,
    body: dict | None = None,
    amendments: tuple[NoteAmendment, ...] = (),
) -> ClinicalNote:
    now = datetime.now(UTC)
    return ClinicalNote(
        id=ClinicalNoteId("note-1"),
        tenant_id=TenantId(tenant),
        case_id=CaseId("case-1"),
        clinical_subject_id=ClinicalSubjectId("subj-1"),
        note_type=ClinicalNoteType.PHONE_CONTACT,
        body=body or {"narrative": "Patient presents with generalised anxiety."},
        author_id=UserId("user-1"),
        created_at=now,
        updated_at=now,
        amendments=amendments,
    )


class TestClinicalNoteEncryptionWiring:
    def test_to_model_persists_ciphertext_not_plaintext(self):
        plaintext = "Patient reports persistent insomnia and intrusive thoughts."
        entity = _make_entity("t-1", body={"narrative": plaintext})

        model = ClinicalNoteMapper.to_model(entity)

        assert model.body is not None
        assert plaintext not in model.body
        assert model.amendments is not None

    def test_round_trip_preserves_the_body(self):
        entity = _make_entity("t-1", body={"narrative": "session content"})
        model = ClinicalNoteMapper.to_model(entity)

        rehydrated = ClinicalNoteMapper.to_entity(model)
        assert rehydrated.body == {"narrative": "session content"}

    def test_round_trip_preserves_amendments(self):
        amendment = NoteAmendment(
            id=NoteAmendmentId("amend-1"),
            author_id=UserId("user-2"),
            body={"narrative": "corrected wording"},
            reason="typo fix",
            created_at=datetime.now(UTC),
        )
        entity = _make_entity("t-1", amendments=(amendment,))
        model = ClinicalNoteMapper.to_model(entity)

        plaintext_reason = "typo fix"
        assert plaintext_reason not in model.amendments

        rehydrated = ClinicalNoteMapper.to_entity(model)
        assert len(rehydrated.amendments) == 1
        assert rehydrated.amendments[0].reason == "typo fix"
        assert rehydrated.amendments[0].body == {"narrative": "corrected wording"}

    def test_empty_amendments_round_trip(self):
        entity = _make_entity("t-1")
        model = ClinicalNoteMapper.to_model(entity)
        rehydrated = ClinicalNoteMapper.to_entity(model)
        assert rehydrated.amendments == ()

    def test_ciphertext_is_tenant_bound(self):
        entity_a = _make_entity("t-A", body={"narrative": "shared text"})
        entity_b = _make_entity("t-B", body={"narrative": "shared text"})
        model_a = ClinicalNoteMapper.to_model(entity_a)
        model_b = ClinicalNoteMapper.to_model(entity_b)
        assert model_a.body != model_b.body

        forged = ClinicalNoteModel(
            id=model_a.id,
            tenant_id="t-B",
            case_id=model_a.case_id,
            clinical_subject_id=model_a.clinical_subject_id,
            note_type=model_a.note_type,
            body=model_a.body,
            author_id=model_a.author_id,
            lock_window_seconds=model_a.lock_window_seconds,
            amendments=model_a.amendments,
            created_at=model_a.created_at,
            updated_at=model_a.updated_at,
        )
        with pytest.raises(EncryptionError):
            ClinicalNoteMapper.to_entity(forged)
