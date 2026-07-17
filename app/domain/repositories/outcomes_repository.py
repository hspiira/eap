"""Outcome-measure + fitness-for-duty + RTW-plan repository ports."""

from app.domain.entities.fitness_for_duty import (
    FitnessForDuty,
    ReturnToWorkPlan,
)
from app.domain.entities.outcome_measure import OutcomeMeasure
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    FitnessForDutyId,
    OutcomeMeasureId,
    ReturnToWorkPlanId,
    TenantId,
)


class OutcomeMeasureRepository(BaseRepository[OutcomeMeasure, OutcomeMeasureId]):
    async def list_for_case(self, tenant_id: TenantId, case_id: CaseId) -> list[OutcomeMeasure]: ...


class FitnessForDutyRepository(BaseRepository[FitnessForDuty, FitnessForDutyId]):
    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[FitnessForDuty]: ...


class ReturnToWorkPlanRepository(BaseRepository[ReturnToWorkPlan, ReturnToWorkPlanId]):
    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[ReturnToWorkPlan]: ...
