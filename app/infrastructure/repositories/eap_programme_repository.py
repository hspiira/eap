"""SQL implementations of the EAP programme + Authorization repositories."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.authorization import Authorization
from app.domain.entities.eap_programme import EAPProgramme
from app.domain.repositories.eap_programme_repository import (
    AuthorizationRepository,
    EAPProgrammeRepository,
)
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ContractId,
    EAPProgrammeId,
    TenantId,
)
from app.infrastructure.mappers.eap_programme_mapper import (
    AuthorizationMapper,
    EAPProgrammeMapper,
)
from app.infrastructure.models.eap_programme_model import (
    AuthorizationModel,
    EAPProgrammeModel,
)


class EAPProgrammeRepositoryImpl(EAPProgrammeRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: EAPProgrammeId) -> EAPProgramme | None:
        row = await self._session.get(EAPProgrammeModel, entity_id.value)
        return EAPProgrammeMapper.to_entity(row) if row else None

    async def save(self, entity: EAPProgramme) -> None:
        existing = await self._session.get(EAPProgrammeModel, entity.id.value)
        new_model = EAPProgrammeMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.contract_id = new_model.contract_id
            existing.name = new_model.name
            existing.effective_from = new_model.effective_from
            existing.effective_until = new_model.effective_until
            existing.geographic_scope = new_model.geographic_scope
            existing.description = new_model.description
            existing.caps = new_model.caps
            existing.eligible_dependent_relations = new_model.eligible_dependent_relations
            existing.is_active = new_model.is_active
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: EAPProgrammeId) -> None:
        existing = await self._session.get(EAPProgrammeModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: EAPProgrammeId) -> bool:
        existing = await self._session.get(EAPProgrammeModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(self, tenant_id: TenantId, *, limit: int = 50) -> list[EAPProgramme]:
        stmt = (
            select(EAPProgrammeModel)
            .where(EAPProgrammeModel.tenant_id == tenant_id.value)
            .order_by(EAPProgrammeModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [EAPProgrammeMapper.to_entity(r) for r in rows]

    async def list_for_contract(
        self, tenant_id: TenantId, contract_id: ContractId
    ) -> list[EAPProgramme]:
        stmt = (
            select(EAPProgrammeModel)
            .where(
                EAPProgrammeModel.tenant_id == tenant_id.value,
                EAPProgrammeModel.contract_id == contract_id.value,
            )
            .order_by(EAPProgrammeModel.effective_from.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [EAPProgrammeMapper.to_entity(r) for r in rows]


class AuthorizationRepositoryImpl(AuthorizationRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: AuthorizationId) -> Authorization | None:
        row = await self._session.get(AuthorizationModel, entity_id.value)
        return AuthorizationMapper.to_entity(row) if row else None

    async def save(self, entity: Authorization) -> None:
        existing = await self._session.get(AuthorizationModel, entity.id.value)
        new_model = AuthorizationMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.case_id = new_model.case_id
            existing.clinical_subject_id = new_model.clinical_subject_id
            existing.programme_id = new_model.programme_id
            existing.service_category = new_model.service_category
            existing.sessions_granted = new_model.sessions_granted
            existing.sessions_used = new_model.sessions_used
            existing.status = new_model.status
            existing.granted_at = new_model.granted_at
            existing.expires_on = new_model.expires_on
            existing.extension_requested_sessions = new_model.extension_requested_sessions
            existing.extension_requested_by = new_model.extension_requested_by
            existing.extension_requested_at = new_model.extension_requested_at
            existing.extension_clinician_signoff = new_model.extension_clinician_signoff
            existing.extension_admin_signoff = new_model.extension_admin_signoff
            existing.extended_at = new_model.extended_at
            existing.closed_at = new_model.closed_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: AuthorizationId) -> None:
        existing = await self._session.get(AuthorizationModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: AuthorizationId) -> bool:
        existing = await self._session.get(AuthorizationModel, entity_id.value)
        return existing is not None

    async def list_for_case(self, tenant_id: TenantId, case_id: CaseId) -> list[Authorization]:
        stmt = (
            select(AuthorizationModel)
            .where(
                AuthorizationModel.tenant_id == tenant_id.value,
                AuthorizationModel.case_id == case_id.value,
            )
            .order_by(AuthorizationModel.granted_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [AuthorizationMapper.to_entity(r) for r in rows]
