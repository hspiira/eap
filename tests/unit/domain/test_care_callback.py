"""Care Callback campaign + outreach FSM tests (Phase 3 #D-CareCallback)."""

from datetime import UTC, date, datetime

import pytest

from app.domain.entities.care_callback_campaign import CareCallbackCampaign
from app.domain.entities.outreach_record import OutreachRecord
from app.domain.enums import (
    CareCallbackCampaignStatus,
    OutreachStatus,
    TriageRiskLevel,
)
from app.domain.events import (
    CareCallbackCampaignActivated,
    CareCallbackCampaignCompleted,
    CareCallbackCampaignCreated,
    CrisisFlagRaised,
    OutreachAssigned,
    OutreachCompleted,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    ClientId,
    OutreachRecordId,
    PersonId,
    TenantId,
    UserId,
)

# ---------- Campaign helpers ----------


def _campaign(
    *,
    status: CareCallbackCampaignStatus = CareCallbackCampaignStatus.DRAFT,
    counsellor_pool: tuple[PersonId, ...] = (PersonId("counsellor-1"),),
    target_count: int = 100,
) -> CareCallbackCampaign:
    now = datetime.now(UTC)
    return CareCallbackCampaign(
        id=CareCallbackCampaignId("cc-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        name="Q3 ABSA wave",
        period_start=date(2026, 7, 1),
        period_end=date(2026, 9, 30),
        target_count=target_count,
        counsellor_pool=counsellor_pool,
        status=status,
        created_by=UserId("usr-1"),
        created_at=now,
        updated_at=now,
    )


class TestCampaignCreation:
    def test_created_event_attached_on_creation(self):
        c = _campaign()
        events = [e for e in c.events if isinstance(e, CareCallbackCampaignCreated)]
        assert len(events) == 1

    def test_period_invariant(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            CareCallbackCampaign(
                id=CareCallbackCampaignId("cc-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                name="x",
                period_start=date(2026, 9, 1),
                period_end=date(2026, 8, 1),
                target_count=10,
                counsellor_pool=(PersonId("p-1"),),
                status=CareCallbackCampaignStatus.DRAFT,
                created_by=UserId("u-1"),
                created_at=now,
                updated_at=now,
            )

    def test_negative_target_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            CareCallbackCampaign(
                id=CareCallbackCampaignId("cc-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                name="x",
                period_start=date(2026, 8, 1),
                period_end=date(2026, 9, 1),
                target_count=-1,
                counsellor_pool=(PersonId("p-1"),),
                status=CareCallbackCampaignStatus.DRAFT,
                created_by=UserId("u-1"),
                created_at=now,
                updated_at=now,
            )


class TestCampaignFSM:
    def test_activate_from_draft(self):
        c = _campaign()
        c.activate()
        assert c.status == CareCallbackCampaignStatus.ACTIVE
        assert c.activated_at is not None
        assert any(isinstance(e, CareCallbackCampaignActivated) for e in c.events)

    def test_cannot_activate_with_empty_pool(self):
        c = _campaign(counsellor_pool=())
        with pytest.raises(DomainError):
            c.activate()

    def test_cannot_activate_completed(self):
        c = _campaign(status=CareCallbackCampaignStatus.COMPLETED)
        with pytest.raises(InvalidStateError):
            c.activate()

    def test_complete_from_active(self):
        c = _campaign()
        c.activate()
        c.complete()
        assert c.status == CareCallbackCampaignStatus.COMPLETED
        assert c.completed_at is not None
        assert any(isinstance(e, CareCallbackCampaignCompleted) for e in c.events)

    def test_cannot_complete_draft(self):
        c = _campaign()
        with pytest.raises(InvalidStateError):
            c.complete()

    def test_archive_from_completed(self):
        c = _campaign()
        c.activate()
        c.complete()
        c.archive()
        assert c.status == CareCallbackCampaignStatus.ARCHIVED

    def test_cannot_archive_active(self):
        c = _campaign()
        c.activate()
        with pytest.raises(InvalidStateError):
            c.archive()

    def test_update_pool_in_active(self):
        c = _campaign()
        c.activate()
        c.update_counsellor_pool((PersonId("p-2"), PersonId("p-3")))
        assert c.counsellor_pool == (PersonId("p-2"), PersonId("p-3"))

    def test_cannot_update_pool_archived(self):
        c = _campaign(status=CareCallbackCampaignStatus.ARCHIVED)
        with pytest.raises(InvalidStateError):
            c.update_counsellor_pool((PersonId("p-2"),))

    def test_progress_ratio(self):
        c = _campaign(target_count=10)
        c.activate()
        for _ in range(3):
            c.increment_completed()
        assert c.completed_count == 3
        assert c.progress_ratio() == pytest.approx(0.3)

    def test_progress_ratio_caps_at_one(self):
        c = _campaign(target_count=2)
        c.activate()
        for _ in range(5):
            c.increment_completed()
        assert c.progress_ratio() == 1.0

    def test_progress_ratio_zero_target(self):
        c = _campaign(target_count=0)
        assert c.progress_ratio() == 0.0


# ---------- Outreach helpers ----------


def _outreach(*, status: OutreachStatus = OutreachStatus.PENDING) -> OutreachRecord:
    now = datetime.now(UTC)
    return OutreachRecord(
        id=OutreachRecordId("o-1"),
        tenant_id=TenantId("t-1"),
        campaign_id=CareCallbackCampaignId("cc-1"),
        person_id=PersonId("person-1"),
        status=status,
        contact_attempts=0,
        created_at=now,
        updated_at=now,
    )


class TestOutreachAssignment:
    def test_assign_emits_event_and_advances_status(self):
        o = _outreach()
        o.assign(PersonId("counsellor-1"))
        assert o.status == OutreachStatus.ASSIGNED
        assert o.counsellor_id == PersonId("counsellor-1")
        assert o.assigned_at is not None
        assert any(isinstance(e, OutreachAssigned) for e in o.events)

    def test_cannot_assign_completed(self):
        o = _outreach(status=OutreachStatus.COMPLETED)
        with pytest.raises(InvalidStateError):
            o.assign(PersonId("counsellor-1"))


class TestOutreachAttempts:
    def test_first_attempt_advances_to_contacted(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.record_attempt()
        assert o.status == OutreachStatus.CONTACTED
        assert o.contact_attempts == 1
        assert o.last_attempted_at is not None

    def test_subsequent_attempts_keep_status(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.record_attempt()
        o.record_attempt()
        o.record_attempt()
        assert o.status == OutreachStatus.CONTACTED
        assert o.contact_attempts == 3

    def test_cannot_attempt_pending(self):
        o = _outreach()
        with pytest.raises(InvalidStateError):
            o.record_attempt()


class TestOutreachTriage:
    def test_triage_payload_recorded(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.record_triage(
            instrument_code="JOSEPH7",
            responses={"q1": 2, "q2": 1},
            scores={"total": 3},
            risk_level=TriageRiskLevel.LOW,
            crisis_flag=False,
        )
        assert o.triage_instrument_code == "JOSEPH7"
        assert o.triage_risk_level == TriageRiskLevel.LOW
        assert o.crisis_flag is False
        assert not any(isinstance(e, CrisisFlagRaised) for e in o.events)

    def test_crisis_flag_emits_event(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.record_triage(
            instrument_code="PHQ9",
            responses={"item9": 2},
            scores={"total": 14},
            risk_level=TriageRiskLevel.CRITICAL,
            crisis_flag=True,
            crisis_reason="PHQ-9 item-9 > 0",
        )
        flags = [e for e in o.events if isinstance(e, CrisisFlagRaised)]
        assert len(flags) == 1
        assert flags[0].risk_level == TriageRiskLevel.CRITICAL.value
        assert "PHQ-9" in flags[0].reason

    def test_cannot_record_triage_terminal(self):
        o = _outreach(status=OutreachStatus.COMPLETED)
        with pytest.raises(InvalidStateError):
            o.record_triage(
                instrument_code="X",
                responses={},
                scores={},
                risk_level=TriageRiskLevel.LOW,
                crisis_flag=False,
            )


class TestOutreachTermination:
    def test_complete_after_attempts(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.record_attempt()
        o.complete(notes="resolved on-call")
        assert o.status == OutreachStatus.COMPLETED
        assert o.notes == "resolved on-call"
        assert any(isinstance(e, OutreachCompleted) for e in o.events)
        assert o.is_terminal()

    def test_unreachable_path(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.record_attempt()
        o.mark_unreachable(notes="no response after 3 tries")
        assert o.status == OutreachStatus.UNREACHABLE

    def test_decline_path(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.record_attempt()
        o.mark_declined(notes="not interested")
        assert o.status == OutreachStatus.DECLINED

    def test_escalate_requires_notes(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        with pytest.raises(DomainError):
            o.escalate("")

    def test_escalate_path(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.escalate("Suicidal ideation expressed; routed to senior counsellor")
        assert o.status == OutreachStatus.ESCALATED

    def test_cannot_terminate_pending(self):
        o = _outreach()
        with pytest.raises(InvalidStateError):
            o.complete()

    def test_cannot_terminate_twice(self):
        o = _outreach()
        o.assign(PersonId("c-1"))
        o.complete()
        with pytest.raises(InvalidStateError):
            o.mark_unreachable()
