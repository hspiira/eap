"""SQL implementation of the clinical case repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.case import Case
from app.domain.repositories.case_repository import CaseRepository
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    PersonId,
    TenantId,
)
from app.infrastructure.mappers.case_mapper import CaseMapper
from app.infrastructure.models.case_model import CaseModel


class CaseRepositoryImpl(CaseRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: CaseId) -> Case | None:
        row = await self._session.get(CaseModel, entity_id.value)
        return CaseMapper.to_entity(row) if row else None

    async def save(self, entity: Case) -> None:
        existing = await self._session.get(CaseModel, entity.id.value)
        new_model = CaseMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.clinical_subject_id = new_model.clinical_subject_id
            existing.client_id = new_model.client_id
            existing.presenting_problem = new_model.presenting_problem
            existing.referral_source = new_model.referral_source
            existing.status = new_model.status
            existing.opened_at = new_model.opened_at
            existing.assigned_counsellor_id = new_model.assigned_counsellor_id
            existing.authorization_id = new_model.authorization_id
            existing.referred_by_user_id = new_model.referred_by_user_id
            existing.referral_notes = new_model.referral_notes
            existing.closed_at = new_model.closed_at
            existing.closure_reason = new_model.closure_reason
            existing.closure_summary_note_id = new_model.closure_summary_note_id
            existing.intake_screener_admin_ids = (
                new_model.intake_screener_admin_ids
            )
            existing.closure_screener_admin_ids = (
                new_model.closure_screener_admin_ids
            )
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: CaseId) -> None:
        existing = await self._session.get(CaseModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: CaseId) -> bool:
        existing = await self._session.get(CaseModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[Case]:
        stmt = (
            select(CaseModel)
            .where(CaseModel.tenant_id == tenant_id.value)
            .order_by(CaseModel.opened_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CaseMapper.to_entity(r) for r in rows]

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[Case]:
        stmt = (
            select(CaseModel)
            .where(
                CaseModel.tenant_id == tenant_id.value,
                CaseModel.clinical_subject_id == subject_id.value,
            )
            .order_by(CaseModel.opened_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CaseMapper.to_entity(r) for r in rows]

    async def list_for_counsellor(
        self,
        tenant_id: TenantId,
        counsellor_id: PersonId,
        *,
        limit: int = 100,
    ) -> list[Case]:
        stmt = (
            select(CaseModel)
            .where(
                CaseModel.tenant_id == tenant_id.value,
                CaseModel.assigned_counsellor_id == counsellor_id.value,
            )
            .order_by(CaseModel.opened_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CaseMapper.to_entity(r) for r in rows]
