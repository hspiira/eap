"""SQL implementations of the manager-workspace repositories."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.manager_workspace import (
    ManagerConsult,
    TrainingEnrolment,
    WorkLifeProvider,
    WorkLifeReferral,
)
from app.domain.enums import WorkLifeServiceType
from app.domain.repositories.manager_workspace_repository import (
    ManagerConsultRepository,
    TrainingEnrolmentRepository,
    WorkLifeProviderRepository,
    WorkLifeReferralRepository,
)
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
from app.infrastructure.mappers.manager_workspace_mappers import (
    ManagerConsultMapper,
    TrainingEnrolmentMapper,
    WorkLifeProviderMapper,
    WorkLifeReferralMapper,
)
from app.infrastructure.models.manager_workspace_models import (
    ManagerConsultModel,
    TrainingEnrolmentModel,
    WorkLifeProviderModel,
    WorkLifeReferralModel,
)


class ManagerConsultRepositoryImpl(ManagerConsultRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: ManagerConsultId) -> ManagerConsult | None:
        row = await self._session.get(ManagerConsultModel, entity_id.value)
        return ManagerConsultMapper.to_entity(row) if row else None

    async def save(self, entity: ManagerConsult) -> None:
        existing = await self._session.get(ManagerConsultModel, entity.id.value)
        new_model = ManagerConsultMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.topic = new_model.topic
            existing.notes = new_model.notes
            existing.client_id = new_model.client_id
            existing.triggered_referral_case_id = new_model.triggered_referral_case_id
            existing.closed_at = new_model.closed_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: ManagerConsultId) -> None:
        existing = await self._session.get(ManagerConsultModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: ManagerConsultId) -> bool:
        existing = await self._session.get(ManagerConsultModel, entity_id.value)
        return existing is not None

    async def list_for_manager(
        self, tenant_id: TenantId, manager_id: PersonId
    ) -> list[ManagerConsult]:
        stmt = (
            select(ManagerConsultModel)
            .where(
                ManagerConsultModel.tenant_id == tenant_id.value,
                ManagerConsultModel.manager_id == manager_id.value,
            )
            .order_by(ManagerConsultModel.consulted_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [ManagerConsultMapper.to_entity(r) for r in rows]


class WorkLifeProviderRepositoryImpl(WorkLifeProviderRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: WorkLifeProviderId) -> WorkLifeProvider | None:
        row = await self._session.get(WorkLifeProviderModel, entity_id.value)
        return WorkLifeProviderMapper.to_entity(row) if row else None

    async def save(self, entity: WorkLifeProvider) -> None:
        existing = await self._session.get(WorkLifeProviderModel, entity.id.value)
        new_model = WorkLifeProviderMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.name = new_model.name
            existing.service_types = new_model.service_types
            existing.is_active = new_model.is_active
            existing.contact_name = new_model.contact_name
            existing.contact_email = new_model.contact_email
            existing.contact_phone = new_model.contact_phone
            existing.coverage_notes = new_model.coverage_notes
            existing.rate_card_notes = new_model.rate_card_notes
            existing.last_verified_at = new_model.last_verified_at
            existing.deactivated_at = new_model.deactivated_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: WorkLifeProviderId) -> None:
        existing = await self._session.get(WorkLifeProviderModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: WorkLifeProviderId) -> bool:
        existing = await self._session.get(WorkLifeProviderModel, entity_id.value)
        return existing is not None

    async def list_for_service(
        self, tenant_id: TenantId, service_type: WorkLifeServiceType
    ) -> list[WorkLifeProvider]:
        rows = await self.list_active(tenant_id)
        return [p for p in rows if service_type in p.service_types]

    async def list_active(self, tenant_id: TenantId) -> list[WorkLifeProvider]:
        stmt = (
            select(WorkLifeProviderModel)
            .where(
                WorkLifeProviderModel.tenant_id == tenant_id.value,
                WorkLifeProviderModel.is_active.is_(True),
            )
            .order_by(WorkLifeProviderModel.name)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [WorkLifeProviderMapper.to_entity(r) for r in rows]


class WorkLifeReferralRepositoryImpl(WorkLifeReferralRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: WorkLifeReferralId) -> WorkLifeReferral | None:
        row = await self._session.get(WorkLifeReferralModel, entity_id.value)
        return WorkLifeReferralMapper.to_entity(row) if row else None

    async def save(self, entity: WorkLifeReferral) -> None:
        existing = await self._session.get(WorkLifeReferralModel, entity.id.value)
        new_model = WorkLifeReferralMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.outcome = new_model.outcome
            existing.referred_provider_id = new_model.referred_provider_id
            existing.case_id = new_model.case_id
            existing.resolution_notes = new_model.resolution_notes
            existing.resolved_at = new_model.resolved_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: WorkLifeReferralId) -> None:
        existing = await self._session.get(WorkLifeReferralModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: WorkLifeReferralId) -> bool:
        existing = await self._session.get(WorkLifeReferralModel, entity_id.value)
        return existing is not None

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[WorkLifeReferral]:
        stmt = (
            select(WorkLifeReferralModel)
            .where(
                WorkLifeReferralModel.tenant_id == tenant_id.value,
                WorkLifeReferralModel.clinical_subject_id == subject_id.value,
            )
            .order_by(WorkLifeReferralModel.requested_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [WorkLifeReferralMapper.to_entity(r) for r in rows]


class TrainingEnrolmentRepositoryImpl(TrainingEnrolmentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: TrainingEnrolmentId) -> TrainingEnrolment | None:
        row = await self._session.get(TrainingEnrolmentModel, entity_id.value)
        return TrainingEnrolmentMapper.to_entity(row) if row else None

    async def save(self, entity: TrainingEnrolment) -> None:
        existing = await self._session.get(TrainingEnrolmentModel, entity.id.value)
        new_model = TrainingEnrolmentMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.status = new_model.status
            existing.completed_at = new_model.completed_at
            existing.expires_on = new_model.expires_on
            existing.revoked_at = new_model.revoked_at
            existing.revoked_reason = new_model.revoked_reason
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: TrainingEnrolmentId) -> None:
        existing = await self._session.get(TrainingEnrolmentModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: TrainingEnrolmentId) -> bool:
        existing = await self._session.get(TrainingEnrolmentModel, entity_id.value)
        return existing is not None

    async def list_for_trainee(
        self, tenant_id: TenantId, trainee_id: UserId
    ) -> list[TrainingEnrolment]:
        stmt = (
            select(TrainingEnrolmentModel)
            .where(
                TrainingEnrolmentModel.tenant_id == tenant_id.value,
                TrainingEnrolmentModel.trainee_id == trainee_id.value,
            )
            .order_by(TrainingEnrolmentModel.enrolled_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [TrainingEnrolmentMapper.to_entity(r) for r in rows]
