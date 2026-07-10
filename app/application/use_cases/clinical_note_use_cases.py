"""Clinical note use cases."""

from __future__ import annotations

from typing import Any

from app.domain.entities.case import Case
from app.domain.entities.clinical_note import ClinicalNote
from app.domain.enums import ClinicalNoteType
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.clinical_note_repository import (
    ClinicalNoteRepository,
)
from app.domain.value_objects.clinical_note_body import (
    DAPBody,
    NarrativeBody,
    SOAPBody,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    NoteAmendmentId,
    SessionId,
    UserId,
)
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


def _resolve_body(note_type: ClinicalNoteType, raw: dict[str, Any]) -> dict[str, Any]:
    if note_type == ClinicalNoteType.DAP:
        return DAPBody(
            data=raw.get("data", ""),
            assessment=raw.get("assessment", ""),
            plan=raw.get("plan", ""),
        ).as_dict()
    if note_type == ClinicalNoteType.SOAP:
        return SOAPBody(
            subjective=raw.get("subjective", ""),
            objective=raw.get("objective", ""),
            assessment=raw.get("assessment", ""),
            plan=raw.get("plan", ""),
        ).as_dict()
    return NarrativeBody(summary=raw.get("summary", "")).as_dict()


async def _load_case_or_404(repo: CaseRepository, case_id: CaseId) -> Case:
    case = await repo.get_by_id(case_id)
    if case is None:
        raise NotFoundError(
            f"Case not found: {case_id.value}",
            resource_type="Case",
            resource_id=case_id.value,
        )
    return case


class CreateClinicalNoteUseCase:
    def __init__(
        self,
        case_repository: CaseRepository,
        note_repository: ClinicalNoteRepository,
    ):
        self._cases = case_repository
        self._notes = note_repository

    async def execute(
        self,
        *,
        case_id: CaseId,
        author_id: UserId,
        note_type: ClinicalNoteType,
        body: dict[str, Any],
        session_id: SessionId | None = None,
    ) -> ClinicalNote:
        case = await _load_case_or_404(self._cases, case_id)
        if case.is_terminal():
            raise DomainError(
                f"Cannot add notes to a {case.status.value} case"
            )
        validated_body = _resolve_body(note_type, body)
        now = utc_now()
        note = ClinicalNote(
            id=ClinicalNoteId(generate_cuid()),
            tenant_id=case.tenant_id,
            case_id=case.id,
            clinical_subject_id=case.clinical_subject_id,
            note_type=note_type,
            body=validated_body,
            author_id=author_id,
            session_id=session_id,
            created_at=now,
            updated_at=now,
        )
        await self._notes.save(note)
        return note


class UpdateDraftNoteBodyUseCase:
    def __init__(self, repository: ClinicalNoteRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        note_id: ClinicalNoteId,
        editor_id: UserId,
        body: dict[str, Any],
    ) -> ClinicalNote:
        note = await self._repo.get_by_id(note_id)
        if note is None:
            raise NotFoundError(
                f"Clinical note not found: {note_id.value}",
                resource_type="ClinicalNote",
                resource_id=note_id.value,
            )
        validated = _resolve_body(note.note_type, body)
        note.update_body(new_body=validated, editor_id=editor_id)
        await self._repo.save(note)
        return note


class SignClinicalNoteUseCase:
    def __init__(self, repository: ClinicalNoteRepository):
        self._repo = repository

    async def execute(
        self, *, note_id: ClinicalNoteId, signer_id: UserId
    ) -> ClinicalNote:
        note = await self._repo.get_by_id(note_id)
        if note is None:
            raise NotFoundError(
                f"Clinical note not found: {note_id.value}",
                resource_type="ClinicalNote",
                resource_id=note_id.value,
            )
        note.sign(signer_id=signer_id)
        await self._repo.save(note)
        return note


class AmendClinicalNoteUseCase:
    def __init__(self, repository: ClinicalNoteRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        note_id: ClinicalNoteId,
        author_id: UserId,
        body: dict[str, Any],
        reason: str,
    ) -> ClinicalNote:
        note = await self._repo.get_by_id(note_id)
        if note is None:
            raise NotFoundError(
                f"Clinical note not found: {note_id.value}",
                resource_type="ClinicalNote",
                resource_id=note_id.value,
            )
        validated = _resolve_body(note.note_type, body)
        note.amend(
            amendment_id=NoteAmendmentId(generate_cuid()),
            author_id=author_id,
            body=validated,
            reason=reason,
        )
        await self._repo.save(note)
        return note
