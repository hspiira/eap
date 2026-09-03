"""SQLAlchemy implementations of the Care Callback repositories (Phase 3 #D-CareCallback)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.care_callback_campaign import CareCallbackCampaign
from app.domain.entities.outreach_record import OutreachRecord
from app.domain.repositories.care_callback_repository import (
    CareCallbackCampaignRepository,
    OutreachRecordRepository,
)
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    OutreachRecordId,
    PersonId,
    TenantId,
)
from app.infrastructure.mappers.care_callback_mapper import (
    CareCallbackCampaignMapper,
    OutreachRecordMapper,
)
from app.infrastructure.models.care_callback_model import (
    CareCallbackCampaignModel,
    OutreachRecordModel,
)


class CareCallbackCampaignRepositoryImpl(CareCallbackCampaignRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: CareCallbackCampaignId) -> CareCallbackCampaign | None:
        row = await self._session.get(CareCallbackCampaignModel, entity_id.value)
        return CareCallbackCampaignMapper.to_entity(row) if row else None

    async def save(self, entity: CareCallbackCampaign) -> None:
        existing = await self._session.get(CareCallbackCampaignModel, entity.id.value)
        if existing is None:
            self._session.add(CareCallbackCampaignMapper.to_model(entity))
        else:
            existing.name = entity.name
            existing.period_start = entity.period_start
            existing.period_end = entity.period_end
            existing.target_count = entity.target_count
            existing.completed_count = entity.completed_count
            existing.counsellor_pool = [pid.value for pid in entity.counsellor_pool]
            existing.status = entity.status
            existing.sampling_notes = entity.sampling_notes
            existing.activated_at = entity.activated_at
            existing.completed_at = entity.completed_at
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: CareCallbackCampaignId) -> None:
        existing = await self._session.get(CareCallbackCampaignModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: CareCallbackCampaignId) -> bool:
        existing = await self._session.get(CareCallbackCampaignModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 50, offset: int = 0
    ) -> list[CareCallbackCampaign]:
        stmt = (
            select(CareCallbackCampaignModel)
            .where(CareCallbackCampaignModel.tenant_id == tenant_id.value)
            .order_by(CareCallbackCampaignModel.period_start.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CareCallbackCampaignMapper.to_entity(r) for r in rows]


class OutreachRecordRepositoryImpl(OutreachRecordRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: OutreachRecordId) -> OutreachRecord | None:
        row = await self._session.get(OutreachRecordModel, entity_id.value)
        return OutreachRecordMapper.to_entity(row) if row else None

    async def save(self, entity: OutreachRecord) -> None:
        existing = await self._session.get(OutreachRecordModel, entity.id.value)
        if existing is None:
            self._session.add(OutreachRecordMapper.to_model(entity))
        else:
            existing.counsellor_id = entity.counsellor_id.value if entity.counsellor_id else None
            existing.status = entity.status
            existing.contact_attempts = entity.contact_attempts
            existing.assigned_at = entity.assigned_at
            existing.last_attempted_at = entity.last_attempted_at
            existing.completed_at = entity.completed_at
            existing.triage_instrument_code = entity.triage_instrument_code
            existing.triage_responses = entity.triage_responses
            existing.triage_scores = entity.triage_scores
            existing.triage_risk_level = entity.triage_risk_level
            existing.crisis_flag = entity.crisis_flag
            existing.notes = entity.notes
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: OutreachRecordId) -> None:
        existing = await self._session.get(OutreachRecordModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: OutreachRecordId) -> bool:
        existing = await self._session.get(OutreachRecordModel, entity_id.value)
        return existing is not None

    async def list_for_campaign(
        self,
        tenant_id: TenantId,
        campaign_id: CareCallbackCampaignId,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[OutreachRecord]:
        stmt = (
            select(OutreachRecordModel)
            .where(
                OutreachRecordModel.tenant_id == tenant_id.value,
                OutreachRecordModel.campaign_id == campaign_id.value,
            )
            .order_by(OutreachRecordModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [OutreachRecordMapper.to_entity(r) for r in rows]

    async def list_for_counsellor(
        self,
        tenant_id: TenantId,
        counsellor_id: PersonId,
        *,
        limit: int = 100,
    ) -> list[OutreachRecord]:
        stmt = (
            select(OutreachRecordModel)
            .where(
                OutreachRecordModel.tenant_id == tenant_id.value,
                OutreachRecordModel.counsellor_id == counsellor_id.value,
            )
            .order_by(OutreachRecordModel.assigned_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [OutreachRecordMapper.to_entity(r) for r in rows]
