"""SQL implementations of the outcomes / FFD / RTW repositories."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.fitness_for_duty import (
    FitnessForDuty,
    ReturnToWorkPlan,
)
from app.domain.entities.outcome_measure import OutcomeMeasure
from app.domain.repositories.outcomes_repository import (
    FitnessForDutyRepository,
    OutcomeMeasureRepository,
    ReturnToWorkPlanRepository,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    FitnessForDutyId,
    OutcomeMeasureId,
    ReturnToWorkPlanId,
    TenantId,
)
from app.infrastructure.mappers.outcomes_mappers import (
    FitnessForDutyMapper,
    OutcomeMeasureMapper,
    ReturnToWorkPlanMapper,
)
from app.infrastructure.models.outcomes_models import (
    FitnessForDutyModel,
    OutcomeMeasureModel,
    ReturnToWorkPlanModel,
)


class OutcomeMeasureRepositoryImpl(OutcomeMeasureRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: OutcomeMeasureId) -> OutcomeMeasure | None:
        row = await self._session.get(OutcomeMeasureModel, entity_id.value)
        return OutcomeMeasureMapper.to_entity(row) if row else None

    async def save(self, entity: OutcomeMeasure) -> None:
        existing = await self._session.get(OutcomeMeasureModel, entity.id.value)
        new_model = OutcomeMeasureMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: OutcomeMeasureId) -> None:
        existing = await self._session.get(OutcomeMeasureModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: OutcomeMeasureId) -> bool:
        existing = await self._session.get(OutcomeMeasureModel, entity_id.value)
        return existing is not None

    async def list_for_case(
        self, tenant_id: TenantId, case_id: CaseId
    ) -> list[OutcomeMeasure]:
        stmt = (
            select(OutcomeMeasureModel)
            .where(
                OutcomeMeasureModel.tenant_id == tenant_id.value,
                OutcomeMeasureModel.case_id == case_id.value,
            )
            .order_by(OutcomeMeasureModel.recorded_at)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [OutcomeMeasureMapper.to_entity(r) for r in rows]


class FitnessForDutyRepositoryImpl(FitnessForDutyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: FitnessForDutyId) -> FitnessForDuty | None:
        row = await self._session.get(FitnessForDutyModel, entity_id.value)
        return FitnessForDutyMapper.to_entity(row) if row else None

    async def save(self, entity: FitnessForDuty) -> None:
        existing = await self._session.get(FitnessForDutyModel, entity.id.value)
        new_model = FitnessForDutyMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.outcome = new_model.outcome
            existing.assessed_at = new_model.assessed_at
            existing.assessor_id = new_model.assessor_id
            existing.accommodation_recommendations = (
                new_model.accommodation_recommendations
            )
            existing.employer_report_at = new_model.employer_report_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: FitnessForDutyId) -> None:
        existing = await self._session.get(FitnessForDutyModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: FitnessForDutyId) -> bool:
        existing = await self._session.get(FitnessForDutyModel, entity_id.value)
        return existing is not None

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[FitnessForDuty]:
        stmt = (
            select(FitnessForDutyModel)
            .where(
                FitnessForDutyModel.tenant_id == tenant_id.value,
                FitnessForDutyModel.clinical_subject_id == subject_id.value,
            )
            .order_by(FitnessForDutyModel.requested_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [FitnessForDutyMapper.to_entity(r) for r in rows]


class ReturnToWorkPlanRepositoryImpl(ReturnToWorkPlanRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(
        self, entity_id: ReturnToWorkPlanId
    ) -> ReturnToWorkPlan | None:
        row = await self._session.get(ReturnToWorkPlanModel, entity_id.value)
        return ReturnToWorkPlanMapper.to_entity(row) if row else None

    async def save(self, entity: ReturnToWorkPlan) -> None:
        existing = await self._session.get(
            ReturnToWorkPlanModel, entity.id.value
        )
        new_model = ReturnToWorkPlanMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.status = new_model.status
            existing.accommodations = new_model.accommodations
            existing.starts_on = new_model.starts_on
            existing.ends_on = new_model.ends_on
            existing.employer_signoff_user_id = new_model.employer_signoff_user_id
            existing.clinician_signoff_user_id = new_model.clinician_signoff_user_id
            existing.activated_at = new_model.activated_at
            existing.completed_at = new_model.completed_at
            existing.cancelled_at = new_model.cancelled_at
            existing.cancellation_reason = new_model.cancellation_reason
            existing.review_at = new_model.review_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: ReturnToWorkPlanId) -> None:
        existing = await self._session.get(
            ReturnToWorkPlanModel, entity_id.value
        )
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: ReturnToWorkPlanId) -> bool:
        existing = await self._session.get(
            ReturnToWorkPlanModel, entity_id.value
        )
        return existing is not None

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[ReturnToWorkPlan]:
        stmt = (
            select(ReturnToWorkPlanModel)
            .where(
                ReturnToWorkPlanModel.tenant_id == tenant_id.value,
                ReturnToWorkPlanModel.clinical_subject_id == subject_id.value,
            )
            .order_by(ReturnToWorkPlanModel.starts_on.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [ReturnToWorkPlanMapper.to_entity(r) for r in rows]
