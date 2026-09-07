"""SQLAlchemy implementations of the Survey repositories (Phase 3 #D-Survey)."""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.survey_campaign import SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.enums import SurveyCampaignStatus
from app.domain.repositories.survey_repository import (
    SurveyCampaignRepository,
    SurveyResponseRepository,
)
from app.domain.value_objects.core import (
    ClientId,
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

_SORTABLE = {
    "created_at": SurveyCampaignModel.created_at,
    "updated_at": SurveyCampaignModel.updated_at,
    "name": SurveyCampaignModel.name,
    "status": SurveyCampaignModel.status,
    "period_start": SurveyCampaignModel.period_start,
    "period_end": SurveyCampaignModel.period_end,
    "response_count": SurveyCampaignModel.response_count,
}


def _filtered(
    stmt: Select,
    tenant_id: TenantId,
    *,
    status: SurveyCampaignStatus | None,
    client_id: ClientId | None,
    search: str | None,
) -> Select:
    """Apply the tenant scope and the list filters shared by list and count."""
    stmt = stmt.where(SurveyCampaignModel.tenant_id == tenant_id.value)
    if status is not None:
        stmt = stmt.where(SurveyCampaignModel.status == status)
    if client_id is not None:
        stmt = stmt.where(SurveyCampaignModel.client_id == client_id.value)
    if search:
        stmt = stmt.where(SurveyCampaignModel.name.ilike(f"%{search}%"))
    return stmt


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
        self,
        tenant_id: TenantId,
        *,
        status: SurveyCampaignStatus | None = None,
        client_id: ClientId | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> list[SurveyCampaign]:
        column = _SORTABLE.get(sort_by, SurveyCampaignModel.created_at)
        stmt = _filtered(
            select(SurveyCampaignModel),
            tenant_id,
            status=status,
            client_id=client_id,
            search=search,
        )
        stmt = (
            stmt.order_by(column.desc() if sort_desc else column.asc()).limit(limit).offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [SurveyCampaignMapper.to_entity(r) for r in rows]

    async def count_for_tenant(
        self,
        tenant_id: TenantId,
        *,
        status: SurveyCampaignStatus | None = None,
        client_id: ClientId | None = None,
        search: str | None = None,
    ) -> int:
        stmt = _filtered(
            select(func.count()).select_from(SurveyCampaignModel),
            tenant_id,
            status=status,
            client_id=client_id,
            search=search,
        )
        return int((await self._session.execute(stmt)).scalar_one())


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
