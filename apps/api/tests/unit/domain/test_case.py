"""Clinical case aggregate tests."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.case import Case
from app.domain.enums import (
    CaseClosureReason,
    CaseReferralSource,
    CaseStatus,
    PresentingProblem,
)
from app.domain.events import (
    CaseAdvanced,
    CaseAssigned,
    CaseClosed,
    CaseOpened,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClientId,
    ClinicalSubjectId,
    PersonId,
    TenantId,
)


def _case(
    *,
    status: CaseStatus = CaseStatus.INTAKE,
    counsellor: PersonId | None = None,
) -> Case:
    now = datetime.now(UTC)
    return Case(
        id=CaseId("case-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        client_id=ClientId("client-1"),
        presenting_problem=PresentingProblem.STRESS,
        referral_source=CaseReferralSource.SELF,
        status=status,
        opened_at=now,
        assigned_counsellor_id=counsellor,
        created_at=now,
        updated_at=now,
    )


class TestCaseCreation:
    def test_emits_opened_event(self):
        c = _case()
        assert any(isinstance(e, CaseOpened) for e in c.events)

    def test_initial_status_is_intake(self):
        assert _case().status == CaseStatus.INTAKE

    def test_is_terminal_recognises_closed(self):
        assert _case(status=CaseStatus.CLOSED).is_terminal()
        assert not _case().is_terminal()


class TestAssignCounsellor:
    def test_emits_event(self):
        c = _case()
        c.events.clear()
        c.assign_counsellor(PersonId("p-1"))
        assert c.assigned_counsellor_id == PersonId("p-1")
        assert any(isinstance(e, CaseAssigned) for e in c.events)

    def test_cannot_assign_on_terminal(self):
        c = _case(status=CaseStatus.CLOSED)
        with pytest.raises(InvalidStateError):
            c.assign_counsellor(PersonId("p-1"))


class TestAttachAuthorization:
    def test_records_authorization(self):
        c = _case()
        c.attach_authorization(AuthorizationId("auth-1"))
        assert c.authorization_id == AuthorizationId("auth-1")

    def test_blocked_on_terminal(self):
        c = _case(status=CaseStatus.CLOSED)
        with pytest.raises(InvalidStateError):
            c.attach_authorization(AuthorizationId("auth-1"))


class TestAdvance:
    def test_intake_to_assessment(self):
        c = _case()
        c.events.clear()
        c.advance(CaseStatus.ASSESSMENT)
        assert c.status == CaseStatus.ASSESSMENT
        assert any(isinstance(e, CaseAdvanced) for e in c.events)

    def test_active_requires_counsellor(self):
        c = _case(status=CaseStatus.ASSESSMENT)
        with pytest.raises(DomainError, match="counsellor"):
            c.advance(CaseStatus.ACTIVE)

    def test_active_succeeds_with_counsellor(self):
        c = _case(status=CaseStatus.ASSESSMENT, counsellor=PersonId("p-1"))
        c.advance(CaseStatus.ACTIVE)
        assert c.status == CaseStatus.ACTIVE

    def test_invalid_transition_rejected(self):
        c = _case()
        with pytest.raises(InvalidStateError, match="Invalid transition"):
            c.advance(CaseStatus.CLOSED)

    def test_terminal_status_blocks_further_transitions(self):
        c = _case(status=CaseStatus.CLOSED)
        with pytest.raises(InvalidStateError):
            c.advance(CaseStatus.REFERRED_OUT)


class TestScreeners:
    def test_intake_screener_record(self):
        c = _case()
        c.record_intake_screener("admin-1")
        c.record_intake_screener("admin-1")
        c.record_intake_screener("admin-2")
        assert c.intake_screener_admin_ids == ("admin-1", "admin-2")

    def test_intake_screener_blocked_after_active(self):
        c = _case(status=CaseStatus.ACTIVE, counsellor=PersonId("p-1"))
        with pytest.raises(InvalidStateError):
            c.record_intake_screener("admin-1")

    def test_closure_screener_only_in_active(self):
        c = _case()
        with pytest.raises(InvalidStateError):
            c.record_closure_screener("admin-1")
        c.assign_counsellor(PersonId("p-1"))
        c.advance(CaseStatus.ASSESSMENT)
        c.advance(CaseStatus.ACTIVE)
        c.record_closure_screener("admin-1")
        assert c.closure_screener_admin_ids == ("admin-1",)


class TestClose:
    def test_intake_to_closed_with_other_reason(self):
        c = _case()
        c.close(reason=CaseClosureReason.CLIENT_DISCONTINUED)
        assert c.status == CaseStatus.CLOSED
        assert c.closure_reason == CaseClosureReason.CLIENT_DISCONTINUED
        assert any(isinstance(e, CaseClosed) for e in c.events)

    def test_active_close_requires_closure_screener_for_goals_met(self):
        c = _case(status=CaseStatus.ASSESSMENT, counsellor=PersonId("p-1"))
        c.advance(CaseStatus.ACTIVE)
        with pytest.raises(DomainError, match="closure screener"):
            c.close(reason=CaseClosureReason.GOALS_MET)
        c.record_closure_screener("admin-1")
        c.close(reason=CaseClosureReason.GOALS_MET)
        assert c.status == CaseStatus.CLOSED

    def test_cannot_double_close(self):
        c = _case(status=CaseStatus.CLOSED)
        with pytest.raises(InvalidStateError):
            c.close(reason=CaseClosureReason.GOALS_MET)


class TestReferOut:
    def test_marks_referred_out(self):
        c = _case()
        c.refer_out(closure_summary_note_id="note-1")
        assert c.status == CaseStatus.REFERRED_OUT
        assert c.closure_reason == CaseClosureReason.REFERRED_OUT
        assert c.closure_summary_note_id == "note-1"
        assert c.closed_at is not None

    def test_does_not_touch_referral_notes(self):
        c = _case()
        c.referral_notes = "Referred by HR due to conduct concerns"
        c.refer_out(closure_summary_note_id="note-1")
        assert c.referral_notes == "Referred by HR due to conduct concerns"

    def test_requires_closure_summary_note_id(self):
        c = _case()
        with pytest.raises(DomainError, match="closure summary note"):
            c.refer_out(closure_summary_note_id="")

    def test_cannot_refer_terminal(self):
        c = _case(status=CaseStatus.CLOSED)
        with pytest.raises(InvalidStateError):
            c.refer_out(closure_summary_note_id="note-1")
