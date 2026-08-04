"""SQL implementation of the crisis contact repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.crisis_contact import CrisisContact
from app.domain.repositories.crisis_contact_repository import (
    CrisisContactRepository,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    TenantId,
)
from app.infrastructure.mappers.crisis_contact_mapper import (
    CrisisContactMapper,
)
from app.infrastructure.models.crisis_contact_model import CrisisContactModel


class CrisisContactRepositoryImpl(CrisisContactRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: CrisisContactId) -> CrisisContact | None:
        row = await self._session.get(CrisisContactModel, entity_id.value)
        return CrisisContactMapper.to_entity(row) if row else None

    async def save(self, entity: CrisisContact) -> None:
        existing = await self._session.get(CrisisContactModel, entity.id.value)
        new_model = CrisisContactMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.contacted_at = new_model.contacted_at
            existing.caller_relation = new_model.caller_relation
            existing.presenting_concern = new_model.presenting_concern
            existing.clinical_subject_id = new_model.clinical_subject_id
            existing.case_id = new_model.case_id
            existing.counsellor_id = new_model.counsellor_id
            existing.cssrs_administered = new_model.cssrs_administered
            existing.risk_assessment_id = new_model.risk_assessment_id
            existing.safety_plan_id = new_model.safety_plan_id
            existing.risk_level = new_model.risk_level
            existing.warm_handoff = new_model.warm_handoff
            existing.dispatched_at = new_model.dispatched_at
            existing.outcome = new_model.outcome
            existing.resolved_at = new_model.resolved_at
            existing.transcript_summary = new_model.transcript_summary
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: CrisisContactId) -> None:
        existing = await self._session.get(CrisisContactModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: CrisisContactId) -> bool:
        existing = await self._session.get(CrisisContactModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[CrisisContact]:
        stmt = (
            select(CrisisContactModel)
            .where(CrisisContactModel.tenant_id == tenant_id.value)
            .order_by(CrisisContactModel.contacted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CrisisContactMapper.to_entity(r) for r in rows]

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[CrisisContact]:
        stmt = (
            select(CrisisContactModel)
            .where(
                CrisisContactModel.tenant_id == tenant_id.value,
                CrisisContactModel.clinical_subject_id == subject_id.value,
            )
            .order_by(CrisisContactModel.contacted_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CrisisContactMapper.to_entity(r) for r in rows]

    async def list_for_case(self, tenant_id: TenantId, case_id: CaseId) -> list[CrisisContact]:
        stmt = (
            select(CrisisContactModel)
            .where(
                CrisisContactModel.tenant_id == tenant_id.value,
                CrisisContactModel.case_id == case_id.value,
            )
            .order_by(CrisisContactModel.contacted_at)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CrisisContactMapper.to_entity(r) for r in rows]
