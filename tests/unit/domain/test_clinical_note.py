"""Clinical note entity tests."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.clinical_note import (
    DEFAULT_LOCK_WINDOW,
    ClinicalNote,
)
from app.domain.enums import ClinicalNoteType
from app.domain.events import (
    ClinicalNoteLocked,
    ClinicalNoteSigned,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.clinical_note_body import (
    DAPBody,
    NarrativeBody,
    SOAPBody,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    ClinicalSubjectId,
    NoteAmendmentId,
    TenantId,
    UserId,
)


def _note(
    *,
    note_type: ClinicalNoteType = ClinicalNoteType.DAP,
    body: dict | None = None,
) -> ClinicalNote:
    now = datetime.now(UTC)
    return ClinicalNote(
        id=ClinicalNoteId("note-1"),
        tenant_id=TenantId("t-1"),
        case_id=CaseId("case-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        note_type=note_type,
        body=body or {"data": "d", "assessment": "a", "plan": "p"},
        author_id=UserId("clin-1"),
        created_at=now,
        updated_at=now,
    )


class TestNoteBodyVOs:
    def test_dap_requires_all_fields(self):
        with pytest.raises(DomainError):
            DAPBody(data="", assessment="a", plan="p")
        DAPBody(data="d", assessment="a", plan="p")

    def test_soap_requires_all_fields(self):
        with pytest.raises(DomainError):
            SOAPBody(subjective="s", objective="o", assessment="", plan="p")
        SOAPBody(subjective="s", objective="o", assessment="a", plan="p")

    def test_narrative_requires_summary(self):
        with pytest.raises(DomainError):
            NarrativeBody(summary="")
        NarrativeBody(summary="x")


class TestNoteCreation:
    def test_body_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            ClinicalNote(
                id=ClinicalNoteId("note-x"),
                tenant_id=TenantId("t-1"),
                case_id=CaseId("c-1"),
                clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
                note_type=ClinicalNoteType.DAP,
                body={},
                author_id=UserId("u-1"),
                created_at=now,
                updated_at=now,
            )

    def test_from_dap_helper(self):
        n = ClinicalNote.from_dap(
            body=DAPBody(data="d", assessment="a", plan="p"),
            id=ClinicalNoteId("note-2"),
            tenant_id=TenantId("t-1"),
            case_id=CaseId("c-1"),
            clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
            author_id=UserId("u-1"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert n.note_type == ClinicalNoteType.DAP

    def test_narrative_rejects_structured_type(self):
        with pytest.raises(DomainError):
            ClinicalNote.from_narrative(
                body=NarrativeBody(summary="x"),
                note_type=ClinicalNoteType.DAP,
                id=ClinicalNoteId("n"),
                tenant_id=TenantId("t-1"),
                case_id=CaseId("c"),
                clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
                author_id=UserId("u"),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )


class TestNoteEdit:
    def test_author_can_edit_draft(self):
        n = _note()
        n.update_body(
            new_body={"data": "d2", "assessment": "a2", "plan": "p2"},
            editor_id=UserId("clin-1"),
        )
        assert n.body["data"] == "d2"

    def test_non_author_cannot_edit(self):
        n = _note()
        with pytest.raises(DomainError, match="Only the author"):
            n.update_body(
                new_body={"data": "d2", "assessment": "a", "plan": "p"},
                editor_id=UserId("clin-2"),
            )

    def test_signed_note_rejects_edit(self):
        n = _note()
        n.sign(signer_id=UserId("clin-1"))
        with pytest.raises(InvalidStateError):
            n.update_body(
                new_body={"data": "d2", "assessment": "a", "plan": "p"},
                editor_id=UserId("clin-1"),
            )


class TestNoteSign:
    def test_emits_event(self):
        n = _note()
        n.events.clear()
        n.sign(signer_id=UserId("clin-1"))
        assert n.is_signed()
        assert any(isinstance(e, ClinicalNoteSigned) for e in n.events)

    def test_double_sign_rejected(self):
        n = _note()
        n.sign(signer_id=UserId("clin-1"))
        with pytest.raises(InvalidStateError):
            n.sign(signer_id=UserId("clin-1"))

    def test_only_author_signs(self):
        n = _note()
        with pytest.raises(DomainError, match="author"):
            n.sign(signer_id=UserId("clin-2"))


class TestNoteLock:
    def test_lock_blocked_before_signature(self):
        n = _note()
        assert n.lock_if_window_passed() is False

    def test_lock_blocked_within_window(self):
        n = _note()
        n.sign(signer_id=UserId("clin-1"))
        assert n.lock_if_window_passed() is False
        assert not n.is_locked()

    def test_lock_succeeds_after_window(self):
        n = _note()
        n.sign(signer_id=UserId("clin-1"))
        n.events.clear()
        future = datetime.now(UTC) + DEFAULT_LOCK_WINDOW + timedelta(minutes=1)
        assert n.lock_if_window_passed(now=future) is True
        assert any(isinstance(e, ClinicalNoteLocked) for e in n.events)


class TestNoteAmend:
    def test_unsigned_rejects_amend(self):
        n = _note()
        with pytest.raises(InvalidStateError):
            n.amend(
                amendment_id=NoteAmendmentId("a-1"),
                author_id=UserId("clin-1"),
                body={"data": "d", "assessment": "a", "plan": "p"},
                reason="typo",
            )

    def test_amend_after_signed(self):
        n = _note()
        n.sign(signer_id=UserId("clin-1"))
        n.amend(
            amendment_id=NoteAmendmentId("a-1"),
            author_id=UserId("clin-1"),
            body={"data": "d2", "assessment": "a", "plan": "p"},
            reason="correction",
        )
        assert len(n.amendments) == 1
        assert n.amendments[0].reason == "correction"

    def test_amend_requires_reason(self):
        n = _note()
        n.sign(signer_id=UserId("clin-1"))
        with pytest.raises(DomainError):
            n.amend(
                amendment_id=NoteAmendmentId("a-1"),
                author_id=UserId("clin-1"),
                body={"data": "d", "assessment": "a", "plan": "p"},
                reason="",
            )
