"""SQL implementations of the risk-safety repositories."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.caring_contact import CaringContact
from app.domain.entities.mandatory_report import MandatoryReport
from app.domain.entities.risk_assessment import RiskAssessment
from app.domain.entities.safety_plan import SafetyPlan
from app.domain.enums import CaringContactOutcome
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
)
from app.infrastructure.mappers.risk_safety_mappers import (
    CaringContactMapper,
    MandatoryReportMapper,
    RiskAssessmentMapper,
    SafetyPlanMapper,
)
from app.infrastructure.models.risk_safety_models import (
    CaringContactModel,
    MandatoryReportModel,
    RiskAssessmentModel,
    SafetyPlanModel,
)


class RiskAssessmentRepositoryImpl(RiskAssessmentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: RiskAssessmentId) -> RiskAssessment | None:
        row = await self._session.get(RiskAssessmentModel, entity_id.value)
        return RiskAssessmentMapper.to_entity(row) if row else None

    async def save(self, entity: RiskAssessment) -> None:
        existing = await self._session.get(RiskAssessmentModel, entity.id.value)
        new_model = RiskAssessmentMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.case_id = new_model.case_id
            existing.crisis_contact_id = new_model.crisis_contact_id
            existing.risk_level = new_model.risk_level
            existing.imminent_harm_to_self = new_model.imminent_harm_to_self
            existing.imminent_harm_to_others = new_model.imminent_harm_to_others
            existing.child_safety_concern = new_model.child_safety_concern
            existing.vulnerable_adult_concern = new_model.vulnerable_adult_concern
            existing.requires_safety_plan = new_model.requires_safety_plan
            existing.requires_mandatory_report = new_model.requires_mandatory_report
            existing.rationale = new_model.rationale
            existing.questionnaire_response_ids = (
                new_model.questionnaire_response_ids
            )
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: RiskAssessmentId) -> None:
        existing = await self._session.get(RiskAssessmentModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: RiskAssessmentId) -> bool:
        existing = await self._session.get(RiskAssessmentModel, entity_id.value)
        return existing is not None

    async def list_for_case(
        self, tenant_id: TenantId, case_id: CaseId
    ) -> list[RiskAssessment]:
        stmt = (
            select(RiskAssessmentModel)
            .where(
                RiskAssessmentModel.tenant_id == tenant_id.value,
                RiskAssessmentModel.case_id == case_id.value,
            )
            .order_by(RiskAssessmentModel.assessed_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [RiskAssessmentMapper.to_entity(r) for r in rows]

    async def list_for_crisis_contact(
        self, tenant_id: TenantId, crisis_contact_id: CrisisContactId
    ) -> list[RiskAssessment]:
        stmt = (
            select(RiskAssessmentModel)
            .where(
                RiskAssessmentModel.tenant_id == tenant_id.value,
                RiskAssessmentModel.crisis_contact_id == crisis_contact_id.value,
            )
            .order_by(RiskAssessmentModel.assessed_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [RiskAssessmentMapper.to_entity(r) for r in rows]


class SafetyPlanRepositoryImpl(SafetyPlanRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: SafetyPlanId) -> SafetyPlan | None:
        row = await self._session.get(SafetyPlanModel, entity_id.value)
        return SafetyPlanMapper.to_entity(row) if row else None

    async def save(self, entity: SafetyPlan) -> None:
        existing = await self._session.get(SafetyPlanModel, entity.id.value)
        new_model = SafetyPlanMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.status = new_model.status
            existing.warning_signs = new_model.warning_signs
            existing.internal_coping_strategies = new_model.internal_coping_strategies
            existing.social_distractions = new_model.social_distractions
            existing.social_contacts_for_help = new_model.social_contacts_for_help
            existing.professional_help_resources = (
                new_model.professional_help_resources
            )
            existing.means_restriction_plan = new_model.means_restriction_plan
            existing.activated_at = new_model.activated_at
            existing.next_review_at = new_model.next_review_at
            existing.reviewed_at = new_model.reviewed_at
            existing.reviewed_by = new_model.reviewed_by
            existing.supersedes_safety_plan_id = new_model.supersedes_safety_plan_id
            existing.superseded_by = new_model.superseded_by
            existing.superseded_at = new_model.superseded_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: SafetyPlanId) -> None:
        existing = await self._session.get(SafetyPlanModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: SafetyPlanId) -> bool:
        existing = await self._session.get(SafetyPlanModel, entity_id.value)
        return existing is not None

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[SafetyPlan]:
        stmt = (
            select(SafetyPlanModel)
            .where(
                SafetyPlanModel.tenant_id == tenant_id.value,
                SafetyPlanModel.clinical_subject_id == subject_id.value,
            )
            .order_by(SafetyPlanModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [SafetyPlanMapper.to_entity(r) for r in rows]


class MandatoryReportRepositoryImpl(MandatoryReportRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: MandatoryReportId) -> MandatoryReport | None:
        row = await self._session.get(MandatoryReportModel, entity_id.value)
        return MandatoryReportMapper.to_entity(row) if row else None

    async def save(self, entity: MandatoryReport) -> None:
        existing = await self._session.get(MandatoryReportModel, entity.id.value)
        new_model = MandatoryReportMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.external_reference_number = (
                new_model.external_reference_number
            )
            existing.contact_email = new_model.contact_email
            existing.contact_phone = new_model.contact_phone
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: MandatoryReportId) -> None:
        existing = await self._session.get(MandatoryReportModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: MandatoryReportId) -> bool:
        existing = await self._session.get(MandatoryReportModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100
    ) -> list[MandatoryReport]:
        stmt = (
            select(MandatoryReportModel)
            .where(MandatoryReportModel.tenant_id == tenant_id.value)
            .order_by(MandatoryReportModel.submitted_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [MandatoryReportMapper.to_entity(r) for r in rows]


class CaringContactRepositoryImpl(CaringContactRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: CaringContactId) -> CaringContact | None:
        row = await self._session.get(CaringContactModel, entity_id.value)
        return CaringContactMapper.to_entity(row) if row else None

    async def save(self, entity: CaringContact) -> None:
        existing = await self._session.get(CaringContactModel, entity.id.value)
        new_model = CaringContactMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.case_id = new_model.case_id
            existing.outcome = new_model.outcome
            existing.attempted_at = new_model.attempted_at
            existing.completed_at = new_model.completed_at
            existing.handled_by = new_model.handled_by
            existing.notes = new_model.notes
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: CaringContactId) -> None:
        existing = await self._session.get(CaringContactModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: CaringContactId) -> bool:
        existing = await self._session.get(CaringContactModel, entity_id.value)
        return existing is not None

    async def list_pending(
        self, tenant_id: TenantId, *, before: object | None = None
    ) -> list[CaringContact]:
        stmt = select(CaringContactModel).where(
            CaringContactModel.tenant_id == tenant_id.value,
            CaringContactModel.outcome == CaringContactOutcome.PENDING.value,
        )
        if isinstance(before, datetime):
            stmt = stmt.where(CaringContactModel.due_at <= before)
        stmt = stmt.order_by(CaringContactModel.due_at)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CaringContactMapper.to_entity(r) for r in rows]

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[CaringContact]:
        stmt = (
            select(CaringContactModel)
            .where(
                CaringContactModel.tenant_id == tenant_id.value,
                CaringContactModel.clinical_subject_id == subject_id.value,
            )
            .order_by(CaringContactModel.due_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CaringContactMapper.to_entity(r) for r in rows]
