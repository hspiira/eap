"""Survey campaign + webhook routes (Phase 3 #D-Survey / SAD §6.4)."""

import json
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_survey_campaign_repository,
    get_survey_response_repository,
    pagination,
)
from app.api.schemas.survey_schemas import (
    SurveyAggregateResponse,
    SurveyCampaignCreate,
    SurveyCampaignListResponse,
    SurveyCampaignResponse,
    SurveyResponseAcceptedResponse,
    WebhookPayload,
)
from app.application.use_cases.survey_use_cases import (
    CreateSurveyCampaignUseCase,
    GetSurveyAggregateUseCase,
    IngestSurveyResponseUseCase,
)
from app.application.use_cases.transitions import (
    SurveyCampaignTransition,
    TransitionUseCase,
)
from app.core.authorization import assert_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.survey_campaign import SurveyCampaign
from app.domain.enums import SurveyCampaignStatus
from app.domain.repositories.survey_repository import (
    SurveyCampaignRepository,
    SurveyResponseRepository,
)
from app.domain.value_objects.core import (
    ClientId,
    SurveyCampaignId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(tags=["surveys"])


def _to_campaign_response(c: SurveyCampaign) -> SurveyCampaignResponse:
    return SurveyCampaignResponse(
        id=c.id.value,
        tenant_id=c.tenant_id.value,
        client_id=c.client_id.value,
        name=c.name,
        source=c.source,
        external_form_id=c.external_form_id,
        status=c.status,
        period_start=c.period_start,
        period_end=c.period_end,
        anonymous=c.anonymous,
        response_count=c.response_count,
        created_by=c.created_by.value,
        activated_at=c.activated_at,
        closed_at=c.closed_at,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.post(
    "/survey-campaigns",
    response_model=SurveyCampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a survey campaign (Draft)",
)
@transactional()
async def create_survey_campaign(
    data: SurveyCampaignCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: SurveyCampaignRepository = Depends(get_survey_campaign_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = CreateSurveyCampaignUseCase(repo)
    campaign = await use_case.execute(
        campaign_id=SurveyCampaignId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        client_id=ClientId(data.client_id),
        name=data.name,
        source=data.source,
        external_form_id=data.external_form_id,
        webhook_secret=data.webhook_secret,
        created_by=UserId(current_user.user_id),
        period_start=data.period_start,
        period_end=data.period_end,
        anonymous=data.anonymous,
    )
    await audit_change(campaign, audit_handler, current_user, request)
    return _to_campaign_response(campaign)


@router.get(
    "/survey-campaigns",
    response_model=SurveyCampaignListResponse,
    summary="List survey campaigns for the current tenant",
)
@readonly()
async def list_survey_campaigns(
    current_user: TokenData = Depends(get_current_user),
    campaign_status: SurveyCampaignStatus | None = Query(None, alias="status"),
    client_id: str | None = Query(None),
    search: str | None = Query(None),
    pg: PageParams = Depends(pagination()),
    sort_by: Literal[
        "created_at", "updated_at", "name", "status", "period_start", "period_end", "response_count"
    ] = Query("created_at"),
    sort_desc: bool = Query(True),
    repo: SurveyCampaignRepository = Depends(get_survey_campaign_repository),
    db: AsyncSession = Depends(get_db),
):
    tenant = TenantId(current_user.tenant_id)
    client = ClientId(client_id) if client_id else None
    rows = await repo.list_for_tenant(
        tenant,
        status=campaign_status,
        client_id=client,
        search=search,
        limit=pg.limit,
        offset=pg.offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    total = await repo.count_for_tenant(
        tenant, status=campaign_status, client_id=client, search=search
    )
    return SurveyCampaignListResponse(
        items=[_to_campaign_response(c) for c in rows],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=pg.offset + pg.limit < total,
    )


@router.get(
    "/survey-campaigns/{campaign_id}",
    response_model=SurveyCampaignResponse,
    summary="Get a single survey campaign",
)
@readonly()
async def get_survey_campaign(
    campaign_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: SurveyCampaignRepository = Depends(get_survey_campaign_repository),
    db: AsyncSession = Depends(get_db),
):
    campaign = await repo.get_by_id(SurveyCampaignId(campaign_id))
    if campaign is None:
        raise HTTPException(status_code=404, detail="Survey campaign not found")
    assert_same_tenant(current_user, campaign.tenant_id.value)
    return _to_campaign_response(campaign)


@router.post(
    "/survey-campaigns/{campaign_id}/activate",
    response_model=SurveyCampaignResponse,
    summary="Activate a draft survey campaign",
)
@transactional()
async def activate_survey_campaign(
    campaign_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: SurveyCampaignRepository = Depends(get_survey_campaign_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "SurveyCampaign")
    campaign = await use_case.execute(
        SurveyCampaignId(campaign_id),
        SurveyCampaignTransition.ACTIVATE,
        tenant_id=current_user.tenant_id,
    )
    await audit_change(campaign, audit_handler, current_user, request)
    return _to_campaign_response(campaign)


@router.post(
    "/survey-campaigns/{campaign_id}/close",
    response_model=SurveyCampaignResponse,
    summary="Close an active survey campaign",
)
@transactional()
async def close_survey_campaign(
    campaign_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: SurveyCampaignRepository = Depends(get_survey_campaign_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "SurveyCampaign")
    campaign = await use_case.execute(
        SurveyCampaignId(campaign_id),
        SurveyCampaignTransition.CLOSE,
        tenant_id=current_user.tenant_id,
    )
    await audit_change(campaign, audit_handler, current_user, request)
    return _to_campaign_response(campaign)


@router.get(
    "/survey-campaigns/{campaign_id}/aggregate",
    response_model=SurveyAggregateResponse,
    summary="Aggregated answer frequencies (no PII)",
)
@readonly()
async def get_survey_aggregate(
    campaign_id: str,
    current_user: TokenData = Depends(get_current_user),
    campaign_repo: SurveyCampaignRepository = Depends(get_survey_campaign_repository),
    response_repo: SurveyResponseRepository = Depends(get_survey_response_repository),
    db: AsyncSession = Depends(get_db),
):
    campaign = await campaign_repo.get_by_id(SurveyCampaignId(campaign_id))
    if campaign is None:
        raise HTTPException(status_code=404, detail="Survey campaign not found")
    assert_same_tenant(current_user, campaign.tenant_id.value)
    use_case = GetSurveyAggregateUseCase(campaign_repo, response_repo)
    return SurveyAggregateResponse(**await use_case.execute(SurveyCampaignId(campaign_id)))


@router.post(
    "/survey-campaigns/{campaign_id}/webhook",
    response_model=SurveyResponseAcceptedResponse,
    summary="Public webhook ingestion (HMAC-verified, idempotent)",
)
@transactional()
async def ingest_survey_response(
    campaign_id: str,
    request: Request,
    x_webhook_signature: str | None = Header(default=None),
    campaign_repo: SurveyCampaignRepository = Depends(get_survey_campaign_repository),
    response_repo: SurveyResponseRepository = Depends(get_survey_response_repository),
    db: AsyncSession = Depends(get_db),
):
    raw = await request.body()
    try:
        parsed = WebhookPayload.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc
    use_case = IngestSurveyResponseUseCase(campaign_repo, response_repo)
    try:
        record, fresh = await use_case.execute(
            campaign_id=SurveyCampaignId(campaign_id),
            signature_header=x_webhook_signature,
            raw_body=raw,
            external_response_id=parsed.external_response_id,
            submitted_at=parsed.submitted_at,
            payload=parsed.answers,
            metrics=parsed.metrics,
        )
    except IngestSurveyResponseUseCase.SignatureInvalid as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return SurveyResponseAcceptedResponse(
        response_id=record.id.value,
        accepted=True,
        duplicate=not fresh,
    )
