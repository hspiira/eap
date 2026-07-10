"""Crisis-layer aggregate tests: CrisisContact / RiskAssessment / SafetyPlan
/ MandatoryReport / CaringContact."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.caring_contact import (
    CARING_CONTACT_CADENCE,
    CaringContact,
)
from app.domain.entities.crisis_contact import CrisisContact
from app.domain.entities.mandatory_report import MandatoryReport
from app.domain.entities.risk_assessment import RiskAssessment
from app.domain.entities.safety_plan import SafetyPlan
from app.domain.enums import (
    CaringContactChannel,
    CaringContactOutcome,
    CrisisCallerRelation,
    CrisisContactOutcome,
    CrisisWarmHandoff,
    MandatoryReportType,
    SafetyPlanStatus,
    TriageRiskLevel,
)
from app.domain.events import (
    CaringContactCompleted,
    CaringContactScheduled,
    CrisisContactClosed,
    CrisisContactLogged,
    MandatoryReportSubmitted,
    RiskAssessmentRecorded,
    SafetyPlanActivated,
    SafetyPlanCreated,
    SafetyPlanReviewed,
    SafetyPlanSuperseded,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaringContactId,
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    MandatoryReportId,
    RiskAssessmentId,
    SafetyPlanId,
    TenantId,
    UserId,
)


def _crisis_contact(**overrides) -> CrisisContact:
    now = datetime.now(UTC)
    base = dict(
        id=CrisisContactId("cc-1"),
        tenant_id=TenantId("t-1"),
        contacted_at=now,
        caller_relation=CrisisCallerRelation.SELF,
        presenting_concern="Acute distress",
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return CrisisContact(**base)


class TestCrisisContact:
    def test_creation_emits_event(self):
        c = _crisis_contact()
        assert any(isinstance(e, CrisisContactLogged) for e in c.events)

    def test_presenting_concern_required(self):
        with pytest.raises(DomainError):
            _crisis_contact(presenting_concern="")

    def test_warm_handoff_records_dispatch(self):
        c = _crisis_contact()
        c.record_warm_handoff(destination=CrisisWarmHandoff.EMERGENCY_DEPARTMENT)
        assert c.warm_handoff == CrisisWarmHandoff.EMERGENCY_DEPARTMENT
        assert c.dispatched_at is not None

    def test_none_handoff_rejected(self):
        c = _crisis_contact()
        with pytest.raises(DomainError):
            c.record_warm_handoff(destination=CrisisWarmHandoff.NONE)

    def test_resolve_emits_event(self):
        c = _crisis_contact()
        c.events.clear()
        c.resolve(outcome=CrisisContactOutcome.INFORMATION_ONLY)
        assert c.is_resolved()
        assert any(isinstance(e, CrisisContactClosed) for e in c.events)

    def test_cannot_resolve_twice(self):
        c = _crisis_contact()
        c.resolve(outcome=CrisisContactOutcome.BOOKED_APPOINTMENT)
        with pytest.raises(InvalidStateError):
            c.resolve(outcome=CrisisContactOutcome.INFORMATION_ONLY)

    def test_record_assessment_blocked_after_resolution(self):
        c = _crisis_contact()
        c.resolve(outcome=CrisisContactOutcome.INFORMATION_ONLY)
        with pytest.raises(InvalidStateError):
            c.record_assessment(
                risk_assessment_id=RiskAssessmentId("ra-1"),
                risk_level=TriageRiskLevel.LOW,
            )


def _assessment(**overrides) -> RiskAssessment:
    now = datetime.now(UTC)
    base = dict(
        id=RiskAssessmentId("ra-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        assessor_id=UserId("clin-1"),
        assessed_at=now,
        risk_level=TriageRiskLevel.LOW,
        imminent_harm_to_self=False,
        imminent_harm_to_others=False,
        child_safety_concern=False,
        vulnerable_adult_concern=False,
        rationale="Routine assessment",
        case_id=CaseId("case-1"),
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return RiskAssessment(**base)


class TestRiskAssessment:
    def test_emits_event(self):
        a = _assessment()
        assert any(isinstance(e, RiskAssessmentRecorded) for e in a.events)

    def test_must_link_to_case_or_crisis(self):
        with pytest.raises(DomainError):
            _assessment(case_id=None, crisis_contact_id=None)

    def test_rationale_required(self):
        with pytest.raises(DomainError):
            _assessment(rationale="")

    def test_self_harm_forces_safety_plan(self):
        a = _assessment(imminent_harm_to_self=True)
        assert a.requires_safety_plan is True
        assert a.requires_mandatory_report is True

    def test_critical_risk_forces_safety_plan(self):
        a = _assessment(risk_level=TriageRiskLevel.CRITICAL)
        assert a.requires_safety_plan is True

    def test_child_safety_forces_mandatory_report(self):
        a = _assessment(child_safety_concern=True)
        assert a.requires_mandatory_report is True


def _safety_plan(**overrides) -> SafetyPlan:
    now = datetime.now(UTC)
    base = dict(
        id=SafetyPlanId("sp-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        clinician_id=UserId("clin-1"),
        status=SafetyPlanStatus.DRAFT,
        warning_signs=("isolation",),
        internal_coping_strategies=("breathing",),
        social_distractions=("call a friend",),
        social_contacts_for_help=({"name": "Alice", "phone": "555-1"},),
        professional_help_resources=({"label": "On-call", "phone": "555-9"},),
        means_restriction_plan=("remove medication from house",),
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return SafetyPlan(**base)


class TestSafetyPlan:
    def test_creation_event(self):
        p = _safety_plan()
        assert any(isinstance(e, SafetyPlanCreated) for e in p.events)

    def test_each_section_required(self):
        with pytest.raises(DomainError):
            _safety_plan(warning_signs=())

    def test_activate_then_review(self):
        p = _safety_plan()
        p.activate()
        assert p.status == SafetyPlanStatus.ACTIVE
        assert any(isinstance(e, SafetyPlanActivated) for e in p.events)
        p.mark_reviewed(reviewer_id=UserId("super-1"))
        assert p.status == SafetyPlanStatus.REVIEWED
        assert p.reviewed_by == UserId("super-1")
        assert any(isinstance(e, SafetyPlanReviewed) for e in p.events)

    def test_cannot_activate_twice(self):
        p = _safety_plan()
        p.activate()
        with pytest.raises(InvalidStateError):
            p.activate()

    def test_supersede(self):
        p = _safety_plan()
        p.activate()
        p.supersede_with(SafetyPlanId("sp-2"))
        assert p.status == SafetyPlanStatus.SUPERSEDED
        assert p.superseded_by == SafetyPlanId("sp-2")
        assert any(isinstance(e, SafetyPlanSuperseded) for e in p.events)

    def test_cannot_supersede_draft(self):
        p = _safety_plan()
        with pytest.raises(InvalidStateError):
            p.supersede_with(SafetyPlanId("sp-2"))

    def test_cannot_supersede_self(self):
        p = _safety_plan()
        p.activate()
        with pytest.raises(DomainError):
            p.supersede_with(p.id)


def _mandatory_report(**overrides) -> MandatoryReport:
    now = datetime.now(UTC)
    base = dict(
        id=MandatoryReportId("mr-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        risk_assessment_id=RiskAssessmentId("ra-1"),
        report_type=MandatoryReportType.CHILD_ABUSE,
        submitted_to="Uganda Police Family Unit",
        submitted_at=now,
        submitted_by=UserId("clin-1"),
        created_at=now,
    )
    base.update(overrides)
    return MandatoryReport(**base)


class TestMandatoryReport:
    def test_emits_event(self):
        r = _mandatory_report()
        assert any(isinstance(e, MandatoryReportSubmitted) for e in r.events)

    def test_submitted_to_required(self):
        with pytest.raises(DomainError):
            _mandatory_report(submitted_to="")


def _caring_contact(**overrides) -> CaringContact:
    now = datetime.now(UTC)
    base = dict(
        id=CaringContactId("car-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        crisis_contact_id=CrisisContactId("cc-1"),
        channel=CaringContactChannel.CALL,
        due_at=now + timedelta(hours=24),
        outcome=CaringContactOutcome.PENDING,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return CaringContact(**base)


class TestCaringContact:
    def test_emits_scheduled_event(self):
        c = _caring_contact()
        assert any(isinstance(e, CaringContactScheduled) for e in c.events)

    def test_cadence_constants(self):
        assert CARING_CONTACT_CADENCE == (
            timedelta(hours=24),
            timedelta(days=7),
            timedelta(days=30),
        )

    def test_record_outcome_emits_completed(self):
        c = _caring_contact()
        c.events.clear()
        c.record_outcome(
            outcome=CaringContactOutcome.COMPLETED,
            handled_by=UserId("clin-1"),
            notes="Spoke to subject; doing OK",
        )
        assert c.outcome == CaringContactOutcome.COMPLETED
        assert c.completed_at is not None
        assert any(isinstance(e, CaringContactCompleted) for e in c.events)

    def test_pending_outcome_rejected(self):
        c = _caring_contact()
        with pytest.raises(DomainError):
            c.record_outcome(
                outcome=CaringContactOutcome.PENDING,
                handled_by=UserId("clin-1"),
            )

    def test_cannot_double_record(self):
        c = _caring_contact()
        c.record_outcome(
            outcome=CaringContactOutcome.COMPLETED,
            handled_by=UserId("clin-1"),
        )
        with pytest.raises(InvalidStateError):
            c.record_outcome(
                outcome=CaringContactOutcome.LOST_CONTACT,
                handled_by=UserId("clin-1"),
            )
