"""Clinical note mapper."""

from datetime import datetime, timedelta

from app.domain.entities.clinical_note import ClinicalNote, NoteAmendment
from app.domain.enums import ClinicalNoteType
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    ClinicalSubjectId,
    NoteAmendmentId,
    SessionId,
    TenantId,
    UserId,
)
from app.infrastructure.models.clinical_note_model import ClinicalNoteModel
from app.shared.utils.datetime import ensure_utc


def _amendment_from_dict(raw: dict) -> NoteAmendment:
    return NoteAmendment(
        id=NoteAmendmentId(raw["id"]),
        author_id=UserId(raw["author_id"]),
        body=raw["body"],
        reason=raw["reason"],
        created_at=ensure_utc(datetime.fromisoformat(raw["created_at"])),
    )


def _amendment_to_dict(a: NoteAmendment) -> dict:
    return {
        "id": a.id.value,
        "author_id": a.author_id.value,
        "body": a.body,
        "reason": a.reason,
        "created_at": ensure_utc(a.created_at).isoformat(),
    }


class ClinicalNoteMapper:
    @staticmethod
    def to_entity(model: ClinicalNoteModel) -> ClinicalNote:
        entity = ClinicalNote(
            id=ClinicalNoteId(model.id),
            tenant_id=TenantId(model.tenant_id),
            case_id=CaseId(model.case_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            note_type=ClinicalNoteType(model.note_type),
            body=model.body,
            author_id=UserId(model.author_id),
            session_id=SessionId(model.session_id) if model.session_id else None,
            signed_at=ensure_utc(model.signed_at) if model.signed_at else None,
            signed_by=UserId(model.signed_by) if model.signed_by else None,
            locked_at=ensure_utc(model.locked_at) if model.locked_at else None,
            lock_window=timedelta(seconds=model.lock_window_seconds),
            amendments=tuple(_amendment_from_dict(a) for a in (model.amendments or [])),
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: ClinicalNote) -> ClinicalNoteModel:
        return ClinicalNoteModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            case_id=entity.case_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            note_type=entity.note_type,
            body=entity.body,
            author_id=entity.author_id.value,
            session_id=entity.session_id.value if entity.session_id else None,
            signed_at=ensure_utc(entity.signed_at) if entity.signed_at else None,
            signed_by=entity.signed_by.value if entity.signed_by else None,
            locked_at=ensure_utc(entity.locked_at) if entity.locked_at else None,
            lock_window_seconds=int(entity.lock_window.total_seconds()),
            amendments=[_amendment_to_dict(a) for a in entity.amendments],
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
