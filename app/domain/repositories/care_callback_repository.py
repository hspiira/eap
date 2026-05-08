"""Care Callback campaign + outreach repository ports (Phase 3 #D-CareCallback)."""

from app.domain.entities.care_callback_campaign import CareCallbackCampaign
from app.domain.entities.outreach_record import OutreachRecord
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    OutreachRecordId,
    PersonId,
    TenantId,
)


class CareCallbackCampaignRepository(
    BaseRepository[CareCallbackCampaign, CareCallbackCampaignId]
):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 50, offset: int = 0
    ) -> list[CareCallbackCampaign]:
        ...


class OutreachRecordRepository(BaseRepository[OutreachRecord, OutreachRecordId]):
    async def list_for_campaign(
        self,
        tenant_id: TenantId,
        campaign_id: CareCallbackCampaignId,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[OutreachRecord]:
        ...

    async def list_for_counsellor(
        self,
        tenant_id: TenantId,
        counsellor_id: PersonId,
        *,
        limit: int = 100,
    ) -> list[OutreachRecord]:
        ...
