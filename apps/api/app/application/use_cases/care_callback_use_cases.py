"""Care Callback use cases (Phase 3 #D-CareCallback).

Bespoke create + sample paths. Lifecycle / outreach transitions flow
through the existing ``TransitionUseCase`` + the new transition enums.
"""

from __future__ import annotations

from datetime import date, datetime

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.care_callback_campaign import CareCallbackCampaign
from app.domain.entities.outreach_record import OutreachRecord
from app.domain.enums import (
    CareCallbackCampaignStatus,
    OutreachStatus,
    TriageInstrumentCode,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.care_callback_repository import (
    CareCallbackCampaignRepository,
    OutreachRecordRepository,
)
from app.domain.services.triage_scoring import score_triage
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    ClientId,
    OutreachRecordId,
    PersonId,
    TenantId,
    UserId,
)
from app.domain.value_objects.triage import QuestionnaireResponse
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class CreateCareCallbackCampaignUseCase(BaseUseCase[CareCallbackCampaign, CareCallbackCampaignId]):
    def __init__(self, repository: CareCallbackCampaignRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        campaign_id: CareCallbackCampaignId,
        tenant_id: TenantId,
        client_id: ClientId,
        name: str,
        period_start: date,
        period_end: date,
        target_count: int,
        counsellor_pool: tuple[PersonId, ...],
        created_by: UserId,
        sampling_notes: str | None = None,
    ) -> CareCallbackCampaign:
        now = utc_now()
        campaign = CareCallbackCampaign(
            id=campaign_id,
            tenant_id=tenant_id,
            client_id=client_id,
            name=name,
            period_start=period_start,
            period_end=period_end,
            target_count=target_count,
            counsellor_pool=counsellor_pool,
            status=CareCallbackCampaignStatus.DRAFT,
            created_by=created_by,
            sampling_notes=sampling_notes,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(campaign)


class EnrolPersonsInCampaignUseCase:
    """Create one ``OutreachRecord`` per supplied person id (bulk enrol)."""

    def __init__(
        self,
        campaign_repository: CareCallbackCampaignRepository,
        outreach_repository: OutreachRecordRepository,
    ):
        self._campaigns = campaign_repository
        self._outreach = outreach_repository

    async def execute(
        self,
        *,
        campaign_id: CareCallbackCampaignId,
        person_ids: list[PersonId],
    ) -> list[OutreachRecord]:
        campaign = await self._campaigns.get_by_id(campaign_id)
        if campaign is None:
            raise NotFoundError(
                f"Care Callback campaign not found: {campaign_id.value}",
                resource_type="CareCallbackCampaign",
                resource_id=campaign_id.value,
            )
        if campaign.status not in {
            CareCallbackCampaignStatus.DRAFT,
            CareCallbackCampaignStatus.ACTIVE,
        }:
            raise DomainError(f"Cannot enrol into a {campaign.status.value} campaign")
        now = utc_now()
        records: list[OutreachRecord] = []
        for person_id in person_ids:
            record = OutreachRecord(
                id=OutreachRecordId(generate_cuid()),
                tenant_id=campaign.tenant_id,
                campaign_id=campaign_id,
                person_id=person_id,
                status=OutreachStatus.PENDING,
                contact_attempts=0,
                created_at=now,
                updated_at=now,
            )
            await self._outreach.save(record)
            records.append(record)
        return records


class GetCampaignSummaryUseCase:
    """Read-side query: campaign + counts of outreach records by status."""

    def __init__(
        self,
        campaign_repository: CareCallbackCampaignRepository,
        outreach_repository: OutreachRecordRepository,
    ):
        self._campaigns = campaign_repository
        self._outreach = outreach_repository

    async def execute(self, campaign_id: CareCallbackCampaignId) -> dict:
        campaign = await self._campaigns.get_by_id(campaign_id)
        if campaign is None:
            raise NotFoundError(
                f"Care Callback campaign not found: {campaign_id.value}",
                resource_type="CareCallbackCampaign",
                resource_id=campaign_id.value,
            )
        records = await self._outreach.list_for_campaign(
            campaign.tenant_id, campaign_id, limit=10_000
        )
        by_status: dict[str, int] = {}
        crisis_flags = 0
        triage_completed = 0
        for r in records:
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
            if r.crisis_flag:
                crisis_flags += 1
            if r.triage_instrument_code is not None:
                triage_completed += 1
        return {
            "campaign_id": campaign.id.value,
            "client_id": campaign.client_id.value,
            "name": campaign.name,
            "status": campaign.status.value,
            "target_count": campaign.target_count,
            "completed_count": campaign.completed_count,
            "progress_ratio": campaign.progress_ratio(),
            "outreach_total": len(records),
            "outreach_by_status": by_status,
            "triage_completed": triage_completed,
            "crisis_flags": crisis_flags,
            "period_start": campaign.period_start.isoformat(),
            "period_end": campaign.period_end.isoformat(),
            "generated_at": _iso(utc_now()),
        }


class ScoreAndRecordTriageUseCase:
    """Score raw Likert responses against the catalogue, then persist to the outreach record.

    Encapsulates the full Phase 3 triage flow: validate answers → compute scores +
    risk + crisis flag → mutate the aggregate via its FSM → save. Returns the
    updated record alongside the computed ``QuestionnaireResponse`` so callers
    (UI, audit, reports) can render the derived classification without recomputing.
    """

    def __init__(self, outreach_repository: OutreachRecordRepository):
        self._outreach = outreach_repository

    async def execute(
        self,
        *,
        outreach_id: OutreachRecordId,
        instrument_code: TriageInstrumentCode,
        responses: dict[str, int],
    ) -> tuple[OutreachRecord, QuestionnaireResponse]:
        record = await self._outreach.get_by_id(outreach_id)
        if record is None:
            raise NotFoundError(
                f"Outreach record not found: {outreach_id.value}",
                resource_type="OutreachRecord",
                resource_id=outreach_id.value,
            )
        try:
            scored = score_triage(instrument_code, responses)
        except (KeyError, ValueError) as exc:
            raise DomainError(str(exc)) from exc
        record.record_triage(
            instrument_code=scored.instrument_code.value,
            responses=scored.responses,
            scores=scored.scores,
            risk_level=scored.risk_level,
            crisis_flag=scored.crisis_flag,
            crisis_reason=scored.crisis_reason,
        )
        await self._outreach.save(record)
        return record, scored


def _iso(value: datetime) -> str:
    return value.isoformat()
