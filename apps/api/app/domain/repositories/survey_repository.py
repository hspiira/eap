"""Survey campaign + response repository ports (Phase 3 #D-Survey)."""

from app.domain.entities.survey_campaign import SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
)


class SurveyCampaignRepository(BaseRepository[SurveyCampaign, SurveyCampaignId]):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 50, offset: int = 0
    ) -> list[SurveyCampaign]: ...


class SurveyResponseRepository(BaseRepository[SurveyResponse, SurveyResponseId]):
    async def find_by_external_id(
        self,
        campaign_id: SurveyCampaignId,
        external_response_id: str,
    ) -> SurveyResponse | None:
        """Idempotency lookup — return the existing row or None."""
        ...

    async def list_for_campaign(
        self,
        tenant_id: TenantId,
        campaign_id: SurveyCampaignId,
        *,
        limit: int = 1_000,
        offset: int = 0,
    ) -> list[SurveyResponse]: ...
