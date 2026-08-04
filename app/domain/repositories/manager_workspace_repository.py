"""Manager-workspace repository ports."""

from app.domain.entities.manager_workspace import (
    ManagerConsult,
    TrainingEnrolment,
    WorkLifeProvider,
    WorkLifeReferral,
)
from app.domain.enums import WorkLifeServiceType
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    ClinicalSubjectId,
    ManagerConsultId,
    PersonId,
    TenantId,
    TrainingEnrolmentId,
    UserId,
    WorkLifeProviderId,
    WorkLifeReferralId,
)


class ManagerConsultRepository(BaseRepository[ManagerConsult, ManagerConsultId]):
    async def list_for_manager(
        self, tenant_id: TenantId, manager_id: PersonId
    ) -> list[ManagerConsult]: ...


class WorkLifeProviderRepository(BaseRepository[WorkLifeProvider, WorkLifeProviderId]):
    async def list_for_service(
        self, tenant_id: TenantId, service_type: WorkLifeServiceType
    ) -> list[WorkLifeProvider]: ...

    async def list_active(self, tenant_id: TenantId) -> list[WorkLifeProvider]: ...


class WorkLifeReferralRepository(BaseRepository[WorkLifeReferral, WorkLifeReferralId]):
    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[WorkLifeReferral]: ...


class TrainingEnrolmentRepository(BaseRepository[TrainingEnrolment, TrainingEnrolmentId]):
    async def list_for_trainee(
        self, tenant_id: TenantId, trainee_id: UserId
    ) -> list[TrainingEnrolment]: ...
