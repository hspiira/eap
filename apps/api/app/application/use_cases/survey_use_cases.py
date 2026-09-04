"""Survey use cases (Phase 3 #D-Survey).

Bespoke create + ingestion paths. Activate / close lifecycle transitions flow
through the existing ``TransitionUseCase`` + ``SurveyCampaignTransition`` enum.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.application.use_cases.base import BaseUseCase
from app.core.webhook_signature import verify_signature
from app.domain.entities.survey_campaign import SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.enums import SurveyCampaignStatus, SurveySource
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.survey_repository import (
    SurveyCampaignRepository,
    SurveyResponseRepository,
)
from app.domain.value_objects.core import (
    ClientId,
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class CreateSurveyCampaignUseCase(BaseUseCase[SurveyCampaign, SurveyCampaignId]):
    def __init__(self, repository: SurveyCampaignRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        campaign_id: SurveyCampaignId,
        tenant_id: TenantId,
        client_id: ClientId,
        name: str,
        source: SurveySource,
        external_form_id: str,
        webhook_secret: str,
        created_by: UserId,
        period_start: date | None = None,
        period_end: date | None = None,
        anonymous: bool = True,
    ) -> SurveyCampaign:
        now = utc_now()
        campaign = SurveyCampaign(
            id=campaign_id,
            tenant_id=tenant_id,
            client_id=client_id,
            name=name,
            source=source,
            external_form_id=external_form_id,
            webhook_secret=webhook_secret,
            status=SurveyCampaignStatus.DRAFT,
            period_start=period_start,
            period_end=period_end,
            anonymous=anonymous,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(campaign)


class IngestSurveyResponseUseCase:
    """HMAC-verified, idempotent ingestion of one webhook delivery.

    Flow:
        1. Resolve the campaign by id (404 if missing).
        2. Verify ``HMAC-SHA256(webhook_secret, raw_body) == header`` (401 on mismatch).
        3. Reject deliveries unless the campaign is ACTIVE.
        4. Idempotency: on existing ``(campaign, external_response_id)`` return the
           original record without mutation.
        5. Otherwise persist the new response and bump the campaign's
           ``response_count``.
    """

    class SignatureInvalid(DomainError):
        """Raised when HMAC verification fails, distinguishable for 401 mapping."""

    def __init__(
        self,
        campaign_repository: SurveyCampaignRepository,
        response_repository: SurveyResponseRepository,
    ):
        self._campaigns = campaign_repository
        self._responses = response_repository

    async def execute(
        self,
        *,
        campaign_id: SurveyCampaignId,
        signature_header: str | None,
        raw_body: bytes,
        external_response_id: str,
        submitted_at: datetime,
        payload: dict[str, Any],
        metrics: dict[str, Any] | None = None,
    ) -> tuple[SurveyResponse, bool]:
        campaign = await self._campaigns.get_by_id(campaign_id)
        if campaign is None:
            raise NotFoundError(
                f"Survey campaign not found: {campaign_id.value}",
                resource_type="SurveyCampaign",
                resource_id=campaign_id.value,
            )
        if not verify_signature(campaign.webhook_secret, raw_body, signature_header):
            raise IngestSurveyResponseUseCase.SignatureInvalid(
                "Webhook signature verification failed"
            )
        if not campaign.is_accepting_responses():
            raise DomainError(
                f"Survey campaign is {campaign.status.value}; not accepting responses"
            )
        if not external_response_id:
            raise DomainError("external_response_id is required")
        existing = await self._responses.find_by_external_id(campaign_id, external_response_id)
        if existing is not None:
            return existing, False
        now = utc_now()
        response = SurveyResponse(
            id=SurveyResponseId(generate_cuid()),
            tenant_id=campaign.tenant_id,
            campaign_id=campaign_id,
            external_response_id=external_response_id,
            submitted_at=submitted_at,
            payload=payload,
            metrics=metrics,
            received_at=now,
        )
        await self._responses.save(response)
        campaign.increment_response_count(now)
        await self._campaigns.save(campaign)
        return response, True


class GetSurveyAggregateUseCase:
    """Read-side aggregation that never exposes individual answers.

    Returns counts + per-question answer-frequency tables, computed entirely
    in-memory from the per-campaign response set. Suitable for renewal packs;
    individual-row inspection is intentionally not surfaced via this path.
    """

    def __init__(
        self,
        campaign_repository: SurveyCampaignRepository,
        response_repository: SurveyResponseRepository,
    ):
        self._campaigns = campaign_repository
        self._responses = response_repository

    async def execute(self, campaign_id: SurveyCampaignId) -> dict[str, Any]:
        campaign = await self._campaigns.get_by_id(campaign_id)
        if campaign is None:
            raise NotFoundError(
                f"Survey campaign not found: {campaign_id.value}",
                resource_type="SurveyCampaign",
                resource_id=campaign_id.value,
            )
        responses = await self._responses.list_for_campaign(
            campaign.tenant_id, campaign_id, limit=10_000
        )
        per_question: dict[str, dict[str, int]] = {}
        for r in responses:
            for k, v in (r.payload or {}).items():
                bucket = per_question.setdefault(k, {})
                key = str(v)
                bucket[key] = bucket.get(key, 0) + 1
        return {
            "campaign_id": campaign.id.value,
            "client_id": campaign.client_id.value,
            "name": campaign.name,
            "status": campaign.status.value,
            "source": campaign.source.value,
            "anonymous": campaign.anonymous,
            "response_total": len(responses),
            "answer_frequencies": per_question,
            "generated_at": utc_now().isoformat(),
        }
