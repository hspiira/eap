"""OutcomeMeasure / FitnessForDuty / ReturnToWorkPlan aggregate tests."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.entities.fitness_for_duty import (
    Accommodation,
    FitnessForDuty,
    ReturnToWorkPlan,
)
from app.domain.entities.outcome_measure import (
    OutcomeMeasure,
    reliable_change_index,
)
from app.domain.enums import (
    FitnessForDutyOutcome,
    ReturnToWorkPlanStatus,
    TriageInstrumentCode,
)
from app.domain.events import (
    FitnessForDutyRequested,
    FitnessForDutyResolved,
    OutcomeMeasureRecorded,
    ReturnToWorkPlanActivated,
    ReturnToWorkPlanCompleted,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalSubjectId,
    FitnessForDutyId,
    OutcomeMeasureId,
    ReturnToWorkPlanId,
    TenantId,
    UserId,
)


def _outcome_measure(**overrides) -> OutcomeMeasure:
    now = datetime.now(UTC)
    base = dict(
        id=OutcomeMeasureId("om-1"),
        tenant_id=TenantId("t-1"),
        case_id=CaseId("case-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        instrument_code=TriageInstrumentCode.PHQ9,
        intake_response_id="r-intake",
        closure_response_id="r-closure",
        pre_score=18.0,
        post_score=8.0,
        delta=-10.0,
        reliable_change_index=-3.2,
        meets_clinically_significant_change=True,
        recorded_at=now,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return OutcomeMeasure(**base)


class TestOutcomeMeasure:
    def test_emits_event(self):
        m = _outcome_measure()
        assert any(isinstance(e, OutcomeMeasureRecorded) for e in m.events)

    def test_response_ids_required(self):
        with pytest.raises(DomainError):
            _outcome_measure(intake_response_id="")

    def test_response_ids_must_differ(self):
        with pytest.raises(DomainError):
            _outcome_measure(intake_response_id="same", closure_response_id="same")


class TestReliableChangeIndex:
    def test_improvement_yields_negative_rci_for_phq9(self):
        rci = reliable_change_index(
            pre_score=18,
            post_score=8,
            instrument_sd=5.0,
            test_retest_reliability=0.84,
        )
        assert rci < -1.96

    def test_zero_change(self):
        rci = reliable_change_index(
            pre_score=10,
            post_score=10,
            instrument_sd=5.0,
            test_retest_reliability=0.84,
        )
        assert rci == 0.0

    def test_invalid_sd(self):
        with pytest.raises(DomainError):
            reliable_change_index(
                pre_score=10,
                post_score=5,
                instrument_sd=0,
                test_retest_reliability=0.84,
            )

    def test_invalid_reliability(self):
        with pytest.raises(DomainError):
            reliable_change_index(
                pre_score=10,
                post_score=5,
                instrument_sd=5,
                test_retest_reliability=2.0,
            )


def _ffd(**overrides) -> FitnessForDuty:
    now = datetime.now(UTC)
    base = dict(
        id=FitnessForDutyId("ffd-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        client_id=ClientId("client-1"),
        requested_at=now,
        requested_by=UserId("hr-1"),
        business_necessity_rationale=(
            "Performance decline after time off; safety-sensitive role"
        ),
        job_role_summary="Truck driver — safety-sensitive (DOT)",
        outcome=FitnessForDutyOutcome.PENDING,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return FitnessForDuty(**base)


class TestFitnessForDuty:
    def test_emits_event(self):
        f = _ffd()
        assert any(isinstance(e, FitnessForDutyRequested) for e in f.events)

    def test_business_necessity_required(self):
        with pytest.raises(DomainError):
            _ffd(business_necessity_rationale="")

    def test_record_outcome_emits_event(self):
        f = _ffd()
        f.events.clear()
        f.record_outcome(
            outcome=FitnessForDutyOutcome.FIT,
            assessor_id=UserId("clin-1"),
        )
        assert f.is_resolved()
        assert f.outcome == FitnessForDutyOutcome.FIT
        assert any(isinstance(e, FitnessForDutyResolved) for e in f.events)

    def test_fit_with_restrictions_requires_accommodations(self):
        f = _ffd()
        with pytest.raises(DomainError, match="accommodation"):
            f.record_outcome(
                outcome=FitnessForDutyOutcome.FIT_WITH_RESTRICTIONS,
                assessor_id=UserId("clin-1"),
            )

    def test_double_record_blocked(self):
        f = _ffd()
        f.record_outcome(
            outcome=FitnessForDutyOutcome.FIT, assessor_id=UserId("clin-1")
        )
        with pytest.raises(InvalidStateError):
            f.record_outcome(
                outcome=FitnessForDutyOutcome.NOT_FIT,
                assessor_id=UserId("clin-1"),
            )

    def test_employer_reported_requires_resolution(self):
        f = _ffd()
        with pytest.raises(InvalidStateError):
            f.mark_employer_reported()


def _rtw_plan(**overrides) -> ReturnToWorkPlan:
    now = datetime.now(UTC)
    accommodations = (
        Accommodation(
            description="reduced hours",
            starts_on=date.today(),
            ends_on=date.today() + timedelta(days=30),
        ),
    )
    base = dict(
        id=ReturnToWorkPlanId("rtw-1"),
        tenant_id=TenantId("t-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        client_id=ClientId("client-1"),
        starts_on=date.today(),
        status=ReturnToWorkPlanStatus.DRAFT,
        accommodations=accommodations,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return ReturnToWorkPlan(**base)


class TestReturnToWorkPlan:
    def test_accommodations_required(self):
        with pytest.raises(DomainError):
            _rtw_plan(accommodations=())

    def test_activate_then_complete(self):
        p = _rtw_plan()
        p.activate(
            employer_signoff_user_id=UserId("hr-1"),
            clinician_signoff_user_id=UserId("clin-1"),
        )
        assert p.status == ReturnToWorkPlanStatus.ACTIVE
        assert any(isinstance(e, ReturnToWorkPlanActivated) for e in p.events)
        p.complete()
        assert p.status == ReturnToWorkPlanStatus.COMPLETED
        assert any(isinstance(e, ReturnToWorkPlanCompleted) for e in p.events)

    def test_activate_requires_distinct_signoffs(self):
        p = _rtw_plan()
        with pytest.raises(DomainError):
            p.activate(
                employer_signoff_user_id=UserId("u-1"),
                clinician_signoff_user_id=UserId("u-1"),
            )

    def test_cancel_requires_reason(self):
        p = _rtw_plan()
        with pytest.raises(DomainError):
            p.cancel(reason="")

    def test_cannot_complete_draft(self):
        p = _rtw_plan()
        with pytest.raises(InvalidStateError):
            p.complete()

    def test_accommodation_validation(self):
        with pytest.raises(DomainError):
            Accommodation(description="", starts_on=date.today())
        with pytest.raises(DomainError):
            Accommodation(
                description="x",
                starts_on=date.today(),
                ends_on=date.today() - timedelta(days=1),
            )
