"""DSAR routes (Phase 4 #DSAR / SAD §6.6 / §8.4)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_dsar_collector,
    get_dsar_request_repository,
    get_dsar_tombstoner,
)
from app.api.schemas.dsar_schemas import (
    DSARRequestCreate,
    DSARRequestResponse,
    RetentionPolicyResponse,
)
from app.application.services.dsar_service import (
    DSARDataCollector,
    DSARTombstoner,
)
from app.application.use_cases.dsar_use_cases import (
    CancelErasureUseCase,
    ExecuteErasureUseCase,
    ExecuteExportUseCase,
    RequestErasureUseCase,
    RequestExportUseCase,
)
from app.core.authorization import assert_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.dsar_request import DSARRequest
from app.domain.repositories.dsar_repository import DSARRequestRepository
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
    UserId,
)
from app.domain.value_objects.retention import (
    DEFAULT_RETENTION_POLICIES,
    ERASURE_REVERSIBLE_WINDOW_DAYS,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/dsar", tags=["dsar"])


def _to_response(req: DSARRequest) -> DSARRequestResponse:
    return DSARRequestResponse(
        id=req.id.value,
        tenant_id=req.tenant_id.value,
        subject_person_id=req.subject_person_id.value,
        request_type=req.request_type,
        status=req.status,
        requested_by=req.requested_by.value,
        started_at=req.started_at,
        completed_at=req.completed_at,
        failed_reason=req.failed_reason,
        erasure_executes_at=req.erasure_executes_at,
        output=req.output,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.get(
    "/retention-policies",
    response_model=list[RetentionPolicyResponse],
    summary="List per-data-class retention policies",
)
@readonly()
async def list_retention_policies(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return [
        RetentionPolicyResponse(
            data_class=p.data_class.value,
            days=p.days,
            rationale=p.rationale,
        )
        for p in DEFAULT_RETENTION_POLICIES
    ]


@router.post(
    "/export",
    response_model=DSARRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a subject-data export request",
)
@transactional()
async def request_export(
    data: DSARRequestCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: DSARRequestRepository = Depends(get_dsar_request_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    req = await RequestExportUseCase(repo).execute(
        request_id=DSARRequestId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        subject_person_id=PersonId(data.subject_person_id),
        requested_by=UserId(current_user.user_id),
    )
    await audit_change(req, audit_handler, current_user, request)
    return _to_response(req)


@router.post(
    "/{request_id}/execute-export",
    response_model=DSARRequestResponse,
    summary="Execute the export pipeline (synchronous v1)",
)
@transactional()
async def execute_export(
    request_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: DSARRequestRepository = Depends(get_dsar_request_repository),
    collector: DSARDataCollector = Depends(get_dsar_collector),
    db: AsyncSession = Depends(get_db),
):
    req = await repo.get_by_id(DSARRequestId(request_id))
    if req is None:
        raise HTTPException(status_code=404, detail="DSAR request not found")
    assert_same_tenant(current_user, req.tenant_id.value)
    out = await ExecuteExportUseCase(repo, collector).execute(DSARRequestId(request_id))
    return _to_response(out)


@router.post(
    "/erasure",
    response_model=DSARRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an erasure request (reversible window applies)",
)
@transactional()
async def request_erasure(
    data: DSARRequestCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: DSARRequestRepository = Depends(get_dsar_request_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    req = await RequestErasureUseCase(repo).execute(
        request_id=DSARRequestId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        subject_person_id=PersonId(data.subject_person_id),
        requested_by=UserId(current_user.user_id),
        reversible_window_days=(
            data.reversible_window_days
            if data.reversible_window_days is not None
            else ERASURE_REVERSIBLE_WINDOW_DAYS
        ),
    )
    await audit_change(req, audit_handler, current_user, request)
    return _to_response(req)


@router.post(
    "/{request_id}/cancel",
    response_model=DSARRequestResponse,
    summary="Cancel an erasure request during the reversible window",
)
@transactional()
async def cancel_erasure(
    request_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: DSARRequestRepository = Depends(get_dsar_request_repository),
    db: AsyncSession = Depends(get_db),
):
    req = await repo.get_by_id(DSARRequestId(request_id))
    if req is None:
        raise HTTPException(status_code=404, detail="DSAR request not found")
    assert_same_tenant(current_user, req.tenant_id.value)
    out = await CancelErasureUseCase(repo).execute(DSARRequestId(request_id))
    return _to_response(out)


@router.post(
    "/{request_id}/execute-erasure",
    response_model=DSARRequestResponse,
    summary="Execute tombstoning after the reversible window has elapsed",
)
@transactional()
async def execute_erasure(
    request_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: DSARRequestRepository = Depends(get_dsar_request_repository),
    tombstoner: DSARTombstoner = Depends(get_dsar_tombstoner),
    db: AsyncSession = Depends(get_db),
):
    req = await repo.get_by_id(DSARRequestId(request_id))
    if req is None:
        raise HTTPException(status_code=404, detail="DSAR request not found")
    assert_same_tenant(current_user, req.tenant_id.value)
    out = await ExecuteErasureUseCase(repo, tombstoner).execute(DSARRequestId(request_id))
    return _to_response(out)


@router.get(
    "",
    response_model=list[DSARRequestResponse],
    summary="List DSAR requests for the current tenant",
)
@readonly()
async def list_dsar_requests(
    current_user: TokenData = Depends(get_current_user),
    repo: DSARRequestRepository = Depends(get_dsar_request_repository),
    db: AsyncSession = Depends(get_db),
):
    rows = await repo.list_for_tenant(TenantId(current_user.tenant_id))
    return [_to_response(r) for r in rows]


@router.get(
    "/{request_id}",
    response_model=DSARRequestResponse,
    summary="Get one DSAR request",
)
@readonly()
async def get_dsar_request(
    request_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: DSARRequestRepository = Depends(get_dsar_request_repository),
    db: AsyncSession = Depends(get_db),
):
    req = await repo.get_by_id(DSARRequestId(request_id))
    if req is None:
        raise HTTPException(status_code=404, detail="DSAR request not found")
    assert_same_tenant(current_user, req.tenant_id.value)
    return _to_response(req)
