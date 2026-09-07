"""Engagement routes (Phase 4 #D-Engagement / SAD §5.2.8)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_engagement_repository,
)
from app.api.schemas.engagement_schemas import (
    DeliverableCreate,
    DeliverableResponse,
    DeliverableStatusUpdate,
    EngagementCreate,
    EngagementResponse,
    EngagementSummaryResponse,
    HoursLogCreate,
    HoursLogResponse,
)
from app.application.use_cases.engagement_use_cases import (
    AddDeliverableUseCase,
    CreateEngagementUseCase,
    GetEngagementSummaryUseCase,
    LogHoursUseCase,
    UpdateDeliverableStatusUseCase,
)
from app.application.use_cases.transitions import (
    EngagementTransition,
    TransitionUseCase,
)
from app.core.authorization import assert_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.engagement import Deliverable, Engagement, HoursLogEntry
from app.domain.repositories.engagement_repository import EngagementRepository
from app.domain.value_objects.core import (
    ClientId,
    DeliverableId,
    EngagementId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(tags=["engagements"])


def _to_deliverable_response(d: Deliverable) -> DeliverableResponse:
    return DeliverableResponse(
        id=d.id.value,
        title=d.title,
        description=d.description,
        due_date=d.due_date,
        status=d.status,
        delivered_at=d.delivered_at,
    )


def _to_hours_response(h: HoursLogEntry) -> HoursLogResponse:
    return HoursLogResponse(
        id=h.id.value,
        user_id=h.user_id.value,
        logged_on=h.logged_on,
        hours=h.hours,
        note=h.note,
    )


def _to_engagement_response(e: Engagement) -> EngagementResponse:
    return EngagementResponse(
        id=e.id.value,
        tenant_id=e.tenant_id.value,
        client_id=e.client_id.value,
        name=e.name,
        description=e.description,
        status=e.status,
        period_start=e.period_start,
        period_end=e.period_end,
        deliverables=[_to_deliverable_response(d) for d in e.deliverables],
        hours_log=[_to_hours_response(h) for h in e.hours_log],
        created_by=e.created_by.value,
        activated_at=e.activated_at,
        delivered_at=e.delivered_at,
        invoiced_at=e.invoiced_at,
        closed_at=e.closed_at,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.post(
    "/engagements",
    response_model=EngagementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Cluster B consultancy engagement (Draft)",
)
@transactional()
async def create_engagement(
    data: EngagementCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = CreateEngagementUseCase(repo)
    engagement = await use_case.execute(
        engagement_id=EngagementId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        client_id=ClientId(data.client_id),
        name=data.name,
        description=data.description,
        period_start=data.period_start,
        period_end=data.period_end,
        created_by=UserId(current_user.user_id),
    )
    await audit_change(engagement, audit_handler, current_user, request)
    return _to_engagement_response(engagement)


@router.get(
    "/engagements",
    response_model=list[EngagementResponse],
    summary="List engagements for the current tenant",
)
@readonly()
async def list_engagements(
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    db: AsyncSession = Depends(get_db),
):
    rows = await repo.list_for_tenant(TenantId(current_user.tenant_id))
    return [_to_engagement_response(e) for e in rows]


@router.get(
    "/engagements/{engagement_id}",
    response_model=EngagementResponse,
    summary="Get a single engagement",
)
@readonly()
async def get_engagement(
    engagement_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    db: AsyncSession = Depends(get_db),
):
    e = await repo.get_by_id(EngagementId(engagement_id))
    if e is None:
        raise HTTPException(status_code=404, detail="Engagement not found")
    assert_same_tenant(current_user, e.tenant_id.value)
    return _to_engagement_response(e)


@router.get(
    "/engagements/{engagement_id}/summary",
    response_model=EngagementSummaryResponse,
    summary="Engagement summary (totals + deliverable mix + hours-by-user)",
)
@readonly()
async def get_engagement_summary(
    engagement_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    db: AsyncSession = Depends(get_db),
):
    e = await repo.get_by_id(EngagementId(engagement_id))
    if e is None:
        raise HTTPException(status_code=404, detail="Engagement not found")
    assert_same_tenant(current_user, e.tenant_id.value)
    return EngagementSummaryResponse(
        **await GetEngagementSummaryUseCase(repo).execute(EngagementId(engagement_id))
    )


@router.post(
    "/engagements/{engagement_id}/deliverables",
    response_model=DeliverableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a deliverable to an engagement",
)
@transactional()
async def add_deliverable(
    engagement_id: str,
    data: DeliverableCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    deliverable = await AddDeliverableUseCase(repo).execute(
        engagement_id=EngagementId(engagement_id),
        title=data.title,
        description=data.description,
        due_date=data.due_date,
    )
    return _to_deliverable_response(deliverable)


@router.patch(
    "/engagements/{engagement_id}/deliverables/{deliverable_id}",
    response_model=DeliverableResponse,
    summary="Update a deliverable's status",
)
@transactional()
async def update_deliverable_status(
    engagement_id: str,
    deliverable_id: str,
    data: DeliverableStatusUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    d = await UpdateDeliverableStatusUseCase(repo).execute(
        engagement_id=EngagementId(engagement_id),
        deliverable_id=DeliverableId(deliverable_id),
        status=data.status,
    )
    return _to_deliverable_response(d)


@router.post(
    "/engagements/{engagement_id}/hours",
    response_model=HoursLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log hours against an engagement",
)
@transactional()
async def log_hours(
    engagement_id: str,
    data: HoursLogCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    entry = await LogHoursUseCase(repo).execute(
        engagement_id=EngagementId(engagement_id),
        user_id=UserId(data.user_id),
        logged_on=data.logged_on,
        hours=data.hours,
        note=data.note,
    )
    return _to_hours_response(entry)


@router.post(
    "/engagements/{engagement_id}/activate",
    response_model=EngagementResponse,
    summary="Activate a draft engagement",
)
@transactional()
async def activate_engagement(
    engagement_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "Engagement")
    engagement = await use_case.execute(EngagementId(engagement_id), EngagementTransition.ACTIVATE)
    await audit_change(engagement, audit_handler, current_user, request)
    return _to_engagement_response(engagement)


@router.post(
    "/engagements/{engagement_id}/deliver",
    response_model=EngagementResponse,
    summary="Mark an active engagement as delivered",
)
@transactional()
async def deliver_engagement(
    engagement_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "Engagement")
    engagement = await use_case.execute(EngagementId(engagement_id), EngagementTransition.DELIVER)
    await audit_change(engagement, audit_handler, current_user, request)
    return _to_engagement_response(engagement)


@router.post(
    "/engagements/{engagement_id}/invoice",
    response_model=EngagementResponse,
    summary="Mark a delivered engagement as invoiced",
)
@transactional()
async def invoice_engagement(
    engagement_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "Engagement")
    engagement = await use_case.execute(EngagementId(engagement_id), EngagementTransition.INVOICE)
    await audit_change(engagement, audit_handler, current_user, request)
    return _to_engagement_response(engagement)


@router.post(
    "/engagements/{engagement_id}/close",
    response_model=EngagementResponse,
    summary="Close an invoiced engagement",
)
@transactional()
async def close_engagement(
    engagement_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: EngagementRepository = Depends(get_engagement_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "Engagement")
    engagement = await use_case.execute(EngagementId(engagement_id), EngagementTransition.CLOSE)
    await audit_change(engagement, audit_handler, current_user, request)
    return _to_engagement_response(engagement)
