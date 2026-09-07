"""SQLAlchemy implementations of the Survey repositories (Phase 3 #D-Survey)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.survey_campaign import SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.repositories.survey_repository import (
    SurveyCampaignRepository,
    SurveyResponseRepository,
)
from app.domain.value_objects.core import (
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
)
from app.infrastructure.mappers.survey_mapper import (
    SurveyCampaignMapper,
    SurveyResponseMapper,
)
from app.infrastructure.models.survey_model import (
    SurveyCampaignModel,
    SurveyResponseModel,
)


class SurveyCampaignRepositoryImpl(SurveyCampaignRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: SurveyCampaignId) -> SurveyCampaign | None:
        row = await self._session.get(SurveyCampaignModel, entity_id.value)
        return SurveyCampaignMapper.to_entity(row) if row else None

    async def save(self, entity: SurveyCampaign) -> None:
        existing = await self._session.get(SurveyCampaignModel, entity.id.value)
        if existing is None:
            self._session.add(SurveyCampaignMapper.to_model(entity))
        else:
            existing.name = entity.name
            existing.source = entity.source
            existing.external_form_id = entity.external_form_id
            existing.webhook_secret = entity.webhook_secret
            existing.status = entity.status
            existing.period_start = entity.period_start
            existing.period_end = entity.period_end
            existing.anonymous = entity.anonymous
            existing.response_count = entity.response_count
            existing.activated_at = entity.activated_at
            existing.closed_at = entity.closed_at
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: SurveyCampaignId) -> None:
        existing = await self._session.get(SurveyCampaignModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: SurveyCampaignId) -> bool:
        existing = await self._session.get(SurveyCampaignModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 50, offset: int = 0
    ) -> list[SurveyCampaign]:
        stmt = (
            select(SurveyCampaignModel)
            .where(SurveyCampaignModel.tenant_id == tenant_id.value)
            .order_by(SurveyCampaignModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [SurveyCampaignMapper.to_entity(r) for r in rows]


class SurveyResponseRepositoryImpl(SurveyResponseRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: SurveyResponseId) -> SurveyResponse | None:
        row = await self._session.get(SurveyResponseModel, entity_id.value)
        return SurveyResponseMapper.to_entity(row) if row else None

    async def save(self, entity: SurveyResponse) -> None:
        existing = await self._session.get(SurveyResponseModel, entity.id.value)
        if existing is None:
            self._session.add(SurveyResponseMapper.to_model(entity))
        else:
            existing.payload = entity.payload
            existing.metrics = entity.metrics
            existing.updated_at = entity.received_at
        await self._session.flush()

    async def delete(self, entity_id: SurveyResponseId) -> None:
        existing = await self._session.get(SurveyResponseModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: SurveyResponseId) -> bool:
        existing = await self._session.get(SurveyResponseModel, entity_id.value)
        return existing is not None

    async def find_by_external_id(
        self,
        campaign_id: SurveyCampaignId,
        external_response_id: str,
    ) -> SurveyResponse | None:
        stmt = select(SurveyResponseModel).where(
            SurveyResponseModel.campaign_id == campaign_id.value,
            SurveyResponseModel.external_response_id == external_response_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return SurveyResponseMapper.to_entity(row) if row else None

    async def list_for_campaign(
        self,
        tenant_id: TenantId,
        campaign_id: SurveyCampaignId,
        *,
        limit: int = 1_000,
        offset: int = 0,
    ) -> list[SurveyResponse]:
        stmt = (
            select(SurveyResponseModel)
            .where(
                SurveyResponseModel.tenant_id == tenant_id.value,
                SurveyResponseModel.campaign_id == campaign_id.value,
            )
            .order_by(SurveyResponseModel.submitted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [SurveyResponseMapper.to_entity(r) for r in rows]
