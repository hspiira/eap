"""Crisis-layer use cases.

A clinician dialling 999 / a hotline operator picking up: log the contact,
score risk, plan for safety, submit any mandatory report, and schedule caring
contacts. Every use case is built so each step can fail without leaving the
contact mid-flight — the aggregate that *should* exist is created or refused,
never partially committed.
"""

from __future__ import annotations

from datetime import datetime

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
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.crisis_contact_repository import (
    CrisisContactRepository,
)
from app.domain.repositories.risk_safety_repository import (
    CaringContactRepository,
    MandatoryReportRepository,
    RiskAssessmentRepository,
    SafetyPlanRepository,
)
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
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class LogCrisisContactUseCase:
    def __init__(self, repository: CrisisContactRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        caller_relation: CrisisCallerRelation,
        presenting_concern: str,
        contacted_at: datetime | None = None,
        clinical_subject_id: ClinicalSubjectId | None = None,
    ) -> CrisisContact:
        now = utc_now()
        contact = CrisisContact(
            id=CrisisContactId(generate_cuid()),
            tenant_id=tenant_id,
            contacted_at=contacted_at or now,
            caller_relation=caller_relation,
            presenting_concern=presenting_concern,
            clinical_subject_id=clinical_subject_id,
            created_at=now,
            updated_at=now,
        )
        await self._repo.save(contact)
        return contact


class RecordWarmHandoffUseCase:
    def __init__(self, repository: CrisisContactRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        crisis_contact_id: CrisisContactId,
        destination: CrisisWarmHandoff,
    ) -> CrisisContact:
        contact = await self._repo.get_by_id(crisis_contact_id)
        if contact is None:
            raise NotFoundError(
                f"Crisis contact not found: {crisis_contact_id.value}",
                resource_type="CrisisContact",
                resource_id=crisis_contact_id.value,
            )
        contact.record_warm_handoff(destination=destination)
        await self._repo.save(contact)
        return contact


class ResolveCrisisContactUseCase:
    def __init__(self, repository: CrisisContactRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        crisis_contact_id: CrisisContactId,
        outcome: CrisisContactOutcome,
        transcript_summary: str | None = None,
    ) -> CrisisContact:
        contact = await self._repo.get_by_id(crisis_contact_id)
        if contact is None:
            raise NotFoundError(
                f"Crisis contact not found: {crisis_contact_id.value}",
                resource_type="CrisisContact",
                resource_id=crisis_contact_id.value,
            )
        contact.resolve(outcome=outcome, transcript_summary=transcript_summary)
        await self._repo.save(contact)
        return contact


class RecordRiskAssessmentUseCase:
    def __init__(
        self,
        risk_repository: RiskAssessmentRepository,
        crisis_repository: CrisisContactRepository,
        case_repository: CaseRepository,
    ):
        self._risks = risk_repository
        self._crises = crisis_repository
        self._cases = case_repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        clinical_subject_id: ClinicalSubjectId,
        assessor_id: UserId,
        risk_level: TriageRiskLevel,
        rationale: str,
        case_id: CaseId | None = None,
        crisis_contact_id: CrisisContactId | None = None,
        imminent_harm_to_self: bool = False,
        imminent_harm_to_others: bool = False,
        child_safety_concern: bool = False,
        vulnerable_adult_concern: bool = False,
        questionnaire_response_ids: tuple[str, ...] = (),
    ) -> RiskAssessment:
        if case_id is None and crisis_contact_id is None:
            raise DomainError("Risk assessment must be linked to a case or crisis contact")
        now = utc_now()
        assessment = RiskAssessment(
            id=RiskAssessmentId(generate_cuid()),
            tenant_id=tenant_id,
            clinical_subject_id=clinical_subject_id,
            case_id=case_id,
            crisis_contact_id=crisis_contact_id,
            assessor_id=assessor_id,
            assessed_at=now,
            risk_level=risk_level,
            imminent_harm_to_self=imminent_harm_to_self,
            imminent_harm_to_others=imminent_harm_to_others,
            child_safety_concern=child_safety_concern,
            vulnerable_adult_concern=vulnerable_adult_concern,
            rationale=rationale,
            questionnaire_response_ids=questionnaire_response_ids,
            created_at=now,
            updated_at=now,
        )
        await self._risks.save(assessment)
        if crisis_contact_id is not None:
            contact = await self._crises.get_by_id(crisis_contact_id)
            if contact is not None and not contact.is_resolved():
                contact.record_assessment(
                    risk_assessment_id=assessment.id,
                    risk_level=risk_level,
                    cssrs_administered=True,
                )
                await self._crises.save(contact)
        return assessment


class CreateSafetyPlanUseCase:
    def __init__(
        self,
        safety_repository: SafetyPlanRepository,
        crisis_repository: CrisisContactRepository,
    ):
        self._plans = safety_repository
        self._crises = crisis_repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        clinical_subject_id: ClinicalSubjectId,
        clinician_id: UserId,
        warning_signs: tuple[str, ...],
        internal_coping_strategies: tuple[str, ...],
        social_distractions: tuple[str, ...],
        social_contacts_for_help: tuple[dict, ...],
        professional_help_resources: tuple[dict, ...],
        means_restriction_plan: tuple[str, ...],
        case_id: CaseId | None = None,
        crisis_contact_id: CrisisContactId | None = None,
        next_review_at: datetime | None = None,
        activate_immediately: bool = True,
    ) -> SafetyPlan:
        now = utc_now()
        plan = SafetyPlan(
            id=SafetyPlanId(generate_cuid()),
            tenant_id=tenant_id,
            clinical_subject_id=clinical_subject_id,
            case_id=case_id,
            crisis_contact_id=crisis_contact_id,
            clinician_id=clinician_id,
            status=SafetyPlanStatus.DRAFT,
            warning_signs=warning_signs,
            internal_coping_strategies=internal_coping_strategies,
            social_distractions=social_distractions,
            social_contacts_for_help=social_contacts_for_help,
            professional_help_resources=professional_help_resources,
            means_restriction_plan=means_restriction_plan,
            next_review_at=next_review_at,
            created_at=now,
            updated_at=now,
        )
        if activate_immediately:
            plan.activate(now=now)
        await self._plans.save(plan)
        if crisis_contact_id is not None:
            contact = await self._crises.get_by_id(crisis_contact_id)
            if contact is not None and not contact.is_resolved():
                contact.attach_safety_plan(plan.id)
                await self._crises.save(contact)
        return plan


class SubmitMandatoryReportUseCase:
    def __init__(
        self,
        report_repository: MandatoryReportRepository,
        risk_repository: RiskAssessmentRepository,
    ):
        self._reports = report_repository
        self._risks = risk_repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        risk_assessment_id: RiskAssessmentId,
        report_type: MandatoryReportType,
        submitted_to: str,
        submitted_by: UserId,
        case_id: CaseId | None = None,
        crisis_contact_id: CrisisContactId | None = None,
        contact_email: str | None = None,
        contact_phone: str | None = None,
        external_reference_number: str | None = None,
    ) -> MandatoryReport:
        risk = await self._risks.get_by_id(risk_assessment_id)
        if risk is None:
            raise NotFoundError(
                f"Risk assessment not found: {risk_assessment_id.value}",
                resource_type="RiskAssessment",
                resource_id=risk_assessment_id.value,
            )
        if not risk.requires_mandatory_report:
            raise DomainError("Underlying risk assessment does not require a mandatory report")
        if risk.tenant_id != tenant_id:
            raise DomainError("Risk assessment tenant does not match the submitting tenant")
        now = utc_now()
        report = MandatoryReport(
            id=MandatoryReportId(generate_cuid()),
            tenant_id=tenant_id,
            clinical_subject_id=risk.clinical_subject_id,
            risk_assessment_id=risk_assessment_id,
            case_id=case_id or risk.case_id,
            crisis_contact_id=crisis_contact_id or risk.crisis_contact_id,
            report_type=report_type,
            submitted_to=submitted_to,
            submitted_at=now,
            submitted_by=submitted_by,
            external_reference_number=external_reference_number,
            contact_email=contact_email,
            contact_phone=contact_phone,
            created_at=now,
        )
        await self._reports.save(report)
        return report


class ScheduleCaringContactsUseCase:
    """Create the default 24h / 7d / 30d follow-up schedule.

    Idempotent against re-runs: returns whatever schedule already exists if
    any caring contacts are already attached to the same crisis-contact, so a
    duplicate call from a retry path doesn't create a second cohort.
    """

    def __init__(
        self,
        caring_repository: CaringContactRepository,
        crisis_repository: CrisisContactRepository,
    ):
        self._caring = caring_repository
        self._crises = crisis_repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        crisis_contact_id: CrisisContactId,
        channel: CaringContactChannel = CaringContactChannel.CALL,
    ) -> list[CaringContact]:
        contact = await self._crises.get_by_id(crisis_contact_id)
        if contact is None:
            raise NotFoundError(
                f"Crisis contact not found: {crisis_contact_id.value}",
                resource_type="CrisisContact",
                resource_id=crisis_contact_id.value,
            )
        if contact.clinical_subject_id is None:
            raise DomainError("Cannot schedule caring contacts without a clinical subject")
        existing = await self._caring.list_for_subject(tenant_id, contact.clinical_subject_id)
        for c in existing:
            if c.crisis_contact_id == crisis_contact_id:
                return [c for c in existing if c.crisis_contact_id == crisis_contact_id]

        now = utc_now()
        scheduled: list[CaringContact] = []
        for delta in CARING_CONTACT_CADENCE:
            entry = CaringContact(
                id=CaringContactId(generate_cuid()),
                tenant_id=tenant_id,
                clinical_subject_id=contact.clinical_subject_id,
                crisis_contact_id=crisis_contact_id,
                case_id=contact.case_id,
                channel=channel,
                due_at=now + delta,
                outcome=CaringContactOutcome.PENDING,
                created_at=now,
                updated_at=now,
            )
            await self._caring.save(entry)
            scheduled.append(entry)
        return scheduled


class RecordCaringContactOutcomeUseCase:
    def __init__(self, repository: CaringContactRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        caring_contact_id: CaringContactId,
        outcome: CaringContactOutcome,
        handled_by: UserId,
        notes: str | None = None,
    ) -> CaringContact:
        contact = await self._repo.get_by_id(caring_contact_id)
        if contact is None:
            raise NotFoundError(
                f"Caring contact not found: {caring_contact_id.value}",
                resource_type="CaringContact",
                resource_id=caring_contact_id.value,
            )
        contact.record_outcome(outcome=outcome, handled_by=handled_by, notes=notes)
        await self._repo.save(contact)
        return contact
