"""Manager-workspace aggregate tests."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.entities.manager_workspace import (
    ManagerConsult,
    TrainingEnrolment,
    WorkLifeProvider,
    WorkLifeReferral,
)
from app.domain.enums import (
    ManagerConsultTopic,
    TrainingEnrolmentStatus,
    WorkLifeReferralOutcome,
    WorkLifeServiceType,
)
from app.domain.events import (
    ManagerConsultLogged,
    ManagerConsultReferralFiled,
    TrainingEnrolmentCompleted,
    TrainingEnrolmentCreated,
    WorkLifeReferralRequested,
    WorkLifeReferralResolved,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    DocumentId,
    ManagerConsultId,
    PersonId,
    TenantId,
    TrainingEnrolmentId,
    UserId,
    WorkLifeProviderId,
    WorkLifeReferralId,
)


def _consult(**overrides) -> ManagerConsult:
    now = datetime.now(UTC)
    base = dict(
        id=ManagerConsultId("mc-1"),
        tenant_id=TenantId("t-1"),
        manager_id=PersonId("mgr-1"),
        consultant_id=UserId("clin-1"),
        topic=ManagerConsultTopic.PERFORMANCE_CONCERN,
        consulted_at=now,
        notes="Manager is concerned about performance decline; advised to refer.",
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return ManagerConsult(**base)


class TestManagerConsult:
    def test_emits_event(self):
        c = _consult()
        assert any(isinstance(e, ManagerConsultLogged) for e in c.events)

    def test_notes_required(self):
        with pytest.raises(DomainError):
            _consult(notes="")

    def test_attach_referral_emits_event(self):
        c = _consult()
        c.events.clear()
        c.attach_referral(CaseId("case-1"))
        assert c.triggered_referral_case_id == CaseId("case-1")
        assert any(
            isinstance(e, ManagerConsultReferralFiled) for e in c.events
        )

    def test_cannot_attach_referral_after_close(self):
        c = _consult()
        c.close()
        with pytest.raises(InvalidStateError):
            c.attach_referral(CaseId("case-1"))

    def test_close_idempotent(self):
        c = _consult()
        c.close()
        first = c.closed_at
        c.close()
        assert c.closed_at == first


def _provider(**overrides) -> WorkLifeProvider:
    now = datetime.now(UTC)
    base = dict(
        id=WorkLifeProviderId("wlp-1"),
        tenant_id=TenantId("t-1"),
        name="Acme Legal Aid",
        service_types=(WorkLifeServiceType.LEGAL,),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return WorkLifeProvider(**base)


class TestWorkLifeProvider:
    def test_at_least_one_service_required(self):
        with pytest.raises(DomainError):
            _provider(service_types=())

    def test_deactivate_then_reactivate(self):
        p = _provider()
        p.deactivate()
        assert p.is_active is False
        assert p.deactivated_at is not None
        p.reactivate()
        assert p.is_active is True
        assert p.deactivated_at is None


def _referral(**overrides) -> WorkLifeReferral:
    now = datetime.now(UTC)
    base = dict(
        id=WorkLifeReferralId("wlr-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        service_type=WorkLifeServiceType.CHILDCARE,
        requested_at=now,
        outcome=WorkLifeReferralOutcome.REQUESTED,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return WorkLifeReferral(**base)


class TestWorkLifeReferral:
    def test_emits_requested_event(self):
        r = _referral()
        assert any(isinstance(e, WorkLifeReferralRequested) for e in r.events)

    def test_assign_provider(self):
        r = _referral()
        r.assign_provider(WorkLifeProviderId("wlp-1"))
        assert r.referred_provider_id == WorkLifeProviderId("wlp-1")
        assert r.outcome == WorkLifeReferralOutcome.ACCEPTED

    def test_resolve_emits_event(self):
        r = _referral()
        r.events.clear()
        r.resolve(outcome=WorkLifeReferralOutcome.COMPLETED, notes="done")
        assert r.outcome == WorkLifeReferralOutcome.COMPLETED
        assert any(isinstance(e, WorkLifeReferralResolved) for e in r.events)

    def test_cannot_resolve_with_requested(self):
        r = _referral()
        with pytest.raises(DomainError):
            r.resolve(outcome=WorkLifeReferralOutcome.REQUESTED)

    def test_cannot_double_resolve(self):
        r = _referral()
        r.resolve(outcome=WorkLifeReferralOutcome.COMPLETED)
        with pytest.raises(InvalidStateError):
            r.resolve(outcome=WorkLifeReferralOutcome.DECLINED)


def _enrolment(**overrides) -> TrainingEnrolment:
    now = datetime.now(UTC)
    base = dict(
        id=TrainingEnrolmentId("te-1"),
        tenant_id=TenantId("t-1"),
        trainee_id=UserId("mgr-1"),
        document_id=DocumentId("doc-1"),
        status=TrainingEnrolmentStatus.ENROLLED,
        enrolled_at=now,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return TrainingEnrolment(**base)


class TestTrainingEnrolment:
    def test_emits_event(self):
        t = _enrolment()
        assert any(isinstance(e, TrainingEnrolmentCreated) for e in t.events)

    def test_mark_completed(self):
        t = _enrolment()
        t.events.clear()
        t.mark_completed(expires_on=date.today() + timedelta(days=365))
        assert t.status == TrainingEnrolmentStatus.COMPLETED
        assert t.completed_at is not None
        assert any(
            isinstance(e, TrainingEnrolmentCompleted) for e in t.events
        )

    def test_mark_expired_idempotent(self):
        t = _enrolment()
        t.mark_completed(expires_on=date.today() - timedelta(days=1))
        flipped = t.mark_expired_if_due()
        assert flipped is True
        assert t.status == TrainingEnrolmentStatus.EXPIRED
        flipped_again = t.mark_expired_if_due()
        assert flipped_again is False

    def test_mark_expired_no_expires(self):
        t = _enrolment()
        t.mark_completed()
        assert t.mark_expired_if_due() is False

    def test_revoke_requires_reason(self):
        t = _enrolment()
        with pytest.raises(DomainError):
            t.revoke(reason="")

    def test_revoke_then_idempotent(self):
        t = _enrolment()
        t.revoke(reason="Manager left organisation")
        assert t.status == TrainingEnrolmentStatus.REVOKED
        t.revoke(reason="duplicate call")
        assert t.status == TrainingEnrolmentStatus.REVOKED
