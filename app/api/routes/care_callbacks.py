"""Care Callback routes (Phase 3 #D-CareCallback)."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_care_callback_campaign_repository,
    get_outreach_record_repository,
)
from app.api.schemas.care_callback_schemas import (
    CampaignSummaryResponse,
    CareCallbackCampaignCreate,
    CareCallbackCampaignResponse,
    CounsellorPoolUpdate,
    EnrolPersonsRequest,
    OutreachAssignRequest,
    OutreachEscalate,
    OutreachRecordResponse,
    OutreachTerminate,
    TriageInstrumentSchema,
    TriageItemSchema,
    TriageRecordRequest,
    TriageScoreRequest,
    TriageScoreResponse,
)
from app.application.use_cases.care_callback_use_cases import (
    CreateCareCallbackCampaignUseCase,
    EnrolPersonsInCampaignUseCase,
    GetCampaignSummaryUseCase,
    ScoreAndRecordTriageUseCase,
)
from app.domain.enums import StageOfChange, TriageInstrumentCode
from app.domain.services.triage_scoring import CATALOGUE, get_instrument
from app.application.use_cases.transitions import (
    CareCallbackCampaignTransition,
    OutreachTransition,
    TransitionUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.care_callback_campaign import CareCallbackCampaign
from app.domain.entities.outreach_record import OutreachRecord
from app.domain.repositories.care_callback_repository import (
    CareCallbackCampaignRepository,
    OutreachRecordRepository,
)
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    ClientId,
    OutreachRecordId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(tags=["care-callbacks"])


def _to_campaign_response(c: CareCallbackCampaign) -> CareCallbackCampaignResponse:
    return CareCallbackCampaignResponse(
        id=c.id.value,
        tenant_id=c.tenant_id.value,
        client_id=c.client_id.value,
        name=c.name,
        period_start=c.period_start,
        period_end=c.period_end,
        target_count=c.target_count,
        completed_count=c.completed_count,
        counsellor_pool=[p.value for p in c.counsellor_pool],
        status=c.status,
        sampling_notes=c.sampling_notes,
        created_by=c.created_by.value,
        activated_at=c.activated_at,
        completed_at=c.completed_at,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _to_outreach_response(r: OutreachRecord) -> OutreachRecordResponse:
    return OutreachRecordResponse(
        id=r.id.value,
        tenant_id=r.tenant_id.value,
        campaign_id=r.campaign_id.value,
        person_id=r.person_id.value,
        counsellor_id=r.counsellor_id.value if r.counsellor_id else None,
        status=r.status,
        contact_attempts=r.contact_attempts,
        assigned_at=r.assigned_at,
        last_attempted_at=r.last_attempted_at,
        completed_at=r.completed_at,
        triage_instrument_code=r.triage_instrument_code,
        triage_risk_level=r.triage_risk_level,
        crisis_flag=r.crisis_flag,
        notes=r.notes,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# ==================== CAMPAIGN ROUTES ====================


@router.post(
    "/care-callback-campaigns",
    response_model=CareCallbackCampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Draft a new Care Callback campaign",
)
@transactional()
async def create_campaign(
    data: CareCallbackCampaignCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    campaign = await CreateCareCallbackCampaignUseCase(repo).execute(
        campaign_id=CareCallbackCampaignId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        client_id=ClientId(data.client_id),
        name=data.name,
        period_start=data.period_start,
        period_end=data.period_end,
        target_count=data.target_count,
        counsellor_pool=tuple(PersonId(p) for p in data.counsellor_pool),
        created_by=UserId(current_user.user_id),
        sampling_notes=data.sampling_notes,
    )
    await audit_entity_operation(
        entity=campaign,
        audit_handler=audit_handler,
        tenant_id=campaign.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_campaign_response(campaign)


@router.post(
    "/care-callback-campaigns/{campaign_id}/activate",
    response_model=CareCallbackCampaignResponse,
    summary="Activate a draft campaign",
)
@transactional()
async def activate_campaign(
    campaign_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "CareCallbackCampaign"
    campaign = await use_case.execute(
        CareCallbackCampaignId(campaign_id),
        CareCallbackCampaignTransition.ACTIVATE,
    )
    await audit_entity_operation(
        entity=campaign,
        audit_handler=audit_handler,
        tenant_id=campaign.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_campaign_response(campaign)


@router.post(
    "/care-callback-campaigns/{campaign_id}/complete",
    response_model=CareCallbackCampaignResponse,
    summary="Complete (close) an active campaign",
)
@transactional()
async def complete_campaign(
    campaign_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "CareCallbackCampaign"
    campaign = await use_case.execute(
        CareCallbackCampaignId(campaign_id),
        CareCallbackCampaignTransition.COMPLETE,
    )
    await audit_entity_operation(
        entity=campaign,
        audit_handler=audit_handler,
        tenant_id=campaign.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_campaign_response(campaign)


@router.post(
    "/care-callback-campaigns/{campaign_id}/archive",
    response_model=CareCallbackCampaignResponse,
    summary="Archive a draft or completed campaign",
)
@transactional()
async def archive_campaign(
    campaign_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "CareCallbackCampaign"
    campaign = await use_case.execute(
        CareCallbackCampaignId(campaign_id),
        CareCallbackCampaignTransition.ARCHIVE,
    )
    await audit_entity_operation(
        entity=campaign,
        audit_handler=audit_handler,
        tenant_id=campaign.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_campaign_response(campaign)


@router.patch(
    "/care-callback-campaigns/{campaign_id}/counsellor-pool",
    response_model=CareCallbackCampaignResponse,
    summary="Replace the counsellor pool",
)
@transactional()
async def update_counsellor_pool(
    campaign_id: str,
    data: CounsellorPoolUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "CareCallbackCampaign"
    campaign = await use_case.execute(
        CareCallbackCampaignId(campaign_id),
        CareCallbackCampaignTransition.UPDATE_COUNSELLOR_POOL,
        pool=tuple(PersonId(p) for p in data.counsellor_pool),
    )
    await audit_entity_operation(
        entity=campaign,
        audit_handler=audit_handler,
        tenant_id=campaign.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_campaign_response(campaign)


@router.get(
    "/care-callback-campaigns/{campaign_id}",
    response_model=CareCallbackCampaignResponse,
    summary="Get a campaign",
)
@readonly()
async def get_campaign(
    campaign_id: str,
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    campaign = await repo.get_by_id(CareCallbackCampaignId(campaign_id))
    if campaign is None:
        raise HTTPException(status_code=404, detail="Care Callback campaign not found")
    return _to_campaign_response(campaign)


@router.get(
    "/care-callback-campaigns/{campaign_id}/summary",
    response_model=CampaignSummaryResponse,
    summary="Aggregated outreach status / triage / crisis stats for the campaign",
)
@readonly()
async def campaign_summary(
    campaign_id: str,
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    outreach_repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    db: AsyncSession = Depends(get_db),
):
    summary = await GetCampaignSummaryUseCase(repo, outreach_repo).execute(
        CareCallbackCampaignId(campaign_id)
    )
    return CampaignSummaryResponse(**summary)


@router.get(
    "/care-callback-campaigns",
    response_model=list[CareCallbackCampaignResponse],
    summary="List campaigns for the current tenant",
)
@readonly()
async def list_campaigns(
    tenant_id: str = Query(..., description="Tenant identifier"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(require_same_tenant),
    repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    campaigns = await repo.list_for_tenant(
        TenantId(tenant_id), limit=limit, offset=offset
    )
    return [_to_campaign_response(c) for c in campaigns]


# ==================== OUTREACH ROUTES ====================


@router.post(
    "/care-callback-campaigns/{campaign_id}/enrol",
    response_model=list[OutreachRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk-enrol persons into a campaign",
)
@transactional()
async def enrol_persons(
    campaign_id: str,
    data: EnrolPersonsRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    campaign_repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    outreach_repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    db: AsyncSession = Depends(get_db),
):
    records = await EnrolPersonsInCampaignUseCase(
        campaign_repo, outreach_repo
    ).execute(
        campaign_id=CareCallbackCampaignId(campaign_id),
        person_ids=[PersonId(p) for p in data.person_ids],
    )
    return [_to_outreach_response(r) for r in records]


@router.post(
    "/outreach-records/{outreach_id}/assign",
    response_model=OutreachRecordResponse,
    summary="Assign an outreach record to a counsellor",
)
@transactional()
async def assign_outreach(
    outreach_id: str,
    data: OutreachAssignRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "OutreachRecord"
    record = await use_case.execute(
        OutreachRecordId(outreach_id),
        OutreachTransition.ASSIGN,
        counsellor_id=PersonId(data.counsellor_id),
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_outreach_response(record)


@router.post(
    "/outreach-records/{outreach_id}/attempts",
    response_model=OutreachRecordResponse,
    summary="Record a contact attempt",
)
@transactional()
async def record_attempt(
    outreach_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "OutreachRecord"
    record = await use_case.execute(
        OutreachRecordId(outreach_id), OutreachTransition.RECORD_ATTEMPT
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_outreach_response(record)


@router.post(
    "/outreach-records/{outreach_id}/triage",
    response_model=OutreachRecordResponse,
    summary="Record a triage instrument response",
)
@transactional()
async def record_triage(
    outreach_id: str,
    data: TriageRecordRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "OutreachRecord"
    record = await use_case.execute(
        OutreachRecordId(outreach_id),
        OutreachTransition.RECORD_TRIAGE,
        instrument_code=data.instrument_code,
        responses=data.responses,
        scores=data.scores,
        risk_level=data.risk_level,
        crisis_flag=data.crisis_flag,
        crisis_reason=data.crisis_reason,
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_outreach_response(record)


# ==================== TRIAGE CATALOGUE + SCORING ROUTES ====================


@router.get(
    "/triage/instruments",
    response_model=list[TriageInstrumentSchema],
    summary="List supported triage instruments",
)
@readonly()
async def list_triage_instruments(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return [
        TriageInstrumentSchema(
            code=q.code,
            version=q.version,
            title=q.title,
            items=[
                TriageItemSchema(
                    code=it.code,
                    text=it.text,
                    min_value=it.min_value,
                    max_value=it.max_value,
                )
                for it in q.items
            ],
        )
        for q in CATALOGUE.values()
    ]


@router.get(
    "/triage/instruments/{code}",
    response_model=TriageInstrumentSchema,
    summary="Fetch a single triage instrument definition",
)
@readonly()
async def get_triage_instrument(
    code: TriageInstrumentCode,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = get_instrument(code)
    return TriageInstrumentSchema(
        code=q.code,
        version=q.version,
        title=q.title,
        items=[
            TriageItemSchema(
                code=it.code,
                text=it.text,
                min_value=it.min_value,
                max_value=it.max_value,
            )
            for it in q.items
        ],
    )


@router.post(
    "/outreach-records/{outreach_id}/triage/score",
    response_model=TriageScoreResponse,
    summary="Score raw triage answers against the catalogue and persist",
)
@transactional()
async def score_and_record_triage(
    outreach_id: str,
    data: TriageScoreRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = ScoreAndRecordTriageUseCase(repo)
    record, scored = await use_case.execute(
        outreach_id=OutreachRecordId(outreach_id),
        instrument_code=data.instrument_code,
        responses=data.responses,
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    stage_value = scored.derived.get("stage_of_change")
    return TriageScoreResponse(
        instrument_code=scored.instrument_code,
        instrument_version=scored.instrument_version,
        risk_level=scored.risk_level,
        crisis_flag=scored.crisis_flag,
        crisis_reason=scored.crisis_reason,
        scores=scored.scores,
        derived=scored.derived,
        stage_of_change=StageOfChange(stage_value) if stage_value else None,
    )


@router.post(
    "/outreach-records/{outreach_id}/complete",
    response_model=OutreachRecordResponse,
    summary="Mark an outreach as completed",
)
@transactional()
async def complete_outreach(
    outreach_id: str,
    data: OutreachTerminate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "OutreachRecord"
    record = await use_case.execute(
        OutreachRecordId(outreach_id),
        OutreachTransition.COMPLETE,
        notes=data.notes,
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_outreach_response(record)


@router.post(
    "/outreach-records/{outreach_id}/unreachable",
    response_model=OutreachRecordResponse,
    summary="Mark an outreach as unreachable",
)
@transactional()
async def mark_unreachable(
    outreach_id: str,
    data: OutreachTerminate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "OutreachRecord"
    record = await use_case.execute(
        OutreachRecordId(outreach_id),
        OutreachTransition.MARK_UNREACHABLE,
        notes=data.notes,
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_outreach_response(record)


@router.post(
    "/outreach-records/{outreach_id}/decline",
    response_model=OutreachRecordResponse,
    summary="Mark an outreach as declined by the person",
)
@transactional()
async def mark_declined(
    outreach_id: str,
    data: OutreachTerminate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "OutreachRecord"
    record = await use_case.execute(
        OutreachRecordId(outreach_id),
        OutreachTransition.MARK_DECLINED,
        notes=data.notes,
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_outreach_response(record)


@router.post(
    "/outreach-records/{outreach_id}/escalate",
    response_model=OutreachRecordResponse,
    summary="Escalate an outreach to a senior counsellor / crisis path",
)
@transactional()
async def escalate_outreach(
    outreach_id: str,
    data: OutreachEscalate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "OutreachRecord"
    record = await use_case.execute(
        OutreachRecordId(outreach_id),
        OutreachTransition.ESCALATE,
        notes=data.notes,
    )
    await audit_entity_operation(
        entity=record,
        audit_handler=audit_handler,
        tenant_id=record.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_outreach_response(record)


@router.get(
    "/outreach-records/{outreach_id}",
    response_model=OutreachRecordResponse,
    summary="Get an outreach record",
)
@readonly()
async def get_outreach(
    outreach_id: str,
    repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    db: AsyncSession = Depends(get_db),
):
    record = await repo.get_by_id(OutreachRecordId(outreach_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Outreach record not found")
    return _to_outreach_response(record)


@router.get(
    "/care-callback-campaigns/{campaign_id}/outreach-records",
    response_model=list[OutreachRecordResponse],
    summary="List outreach records for a campaign",
)
@readonly()
async def list_campaign_outreach(
    campaign_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    campaign_repo: CareCallbackCampaignRepository = Depends(
        get_care_callback_campaign_repository
    ),
    outreach_repo: OutreachRecordRepository = Depends(get_outreach_record_repository),
    db: AsyncSession = Depends(get_db),
):
    campaign = await campaign_repo.get_by_id(CareCallbackCampaignId(campaign_id))
    if campaign is None:
        raise HTTPException(status_code=404, detail="Care Callback campaign not found")
    offset = (page - 1) * limit
    records = await outreach_repo.list_for_campaign(
        campaign.tenant_id,
        campaign.id,
        limit=limit,
        offset=offset,
    )
    return [_to_outreach_response(r) for r in records]
