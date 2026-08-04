"""SQL implementation of the clinical note repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.clinical_note import ClinicalNote
from app.domain.repositories.clinical_note_repository import (
    ClinicalNoteRepository,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    TenantId,
)
from app.infrastructure.mappers.clinical_note_mapper import ClinicalNoteMapper
from app.infrastructure.models.clinical_note_model import ClinicalNoteModel


class ClinicalNoteRepositoryImpl(ClinicalNoteRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: ClinicalNoteId) -> ClinicalNote | None:
        row = await self._session.get(ClinicalNoteModel, entity_id.value)
        return ClinicalNoteMapper.to_entity(row) if row else None

    async def save(self, entity: ClinicalNote) -> None:
        existing = await self._session.get(ClinicalNoteModel, entity.id.value)
        new_model = ClinicalNoteMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.body = new_model.body
            existing.signed_at = new_model.signed_at
            existing.signed_by = new_model.signed_by
            existing.locked_at = new_model.locked_at
            existing.lock_window_seconds = new_model.lock_window_seconds
            existing.amendments = new_model.amendments
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: ClinicalNoteId) -> None:
        existing = await self._session.get(ClinicalNoteModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: ClinicalNoteId) -> bool:
        existing = await self._session.get(ClinicalNoteModel, entity_id.value)
        return existing is not None

    async def list_for_case(self, tenant_id: TenantId, case_id: CaseId) -> list[ClinicalNote]:
        stmt = (
            select(ClinicalNoteModel)
            .where(
                ClinicalNoteModel.tenant_id == tenant_id.value,
                ClinicalNoteModel.case_id == case_id.value,
            )
            .order_by(ClinicalNoteModel.created_at)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [ClinicalNoteMapper.to_entity(r) for r in rows]
