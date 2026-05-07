"""
Service Session API Routes

FastAPI routes for Service Session operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import (
    get_service_session_for_current_tenant,
    require_same_tenant,
)
from app.core.security import TokenData, get_current_user

from app.api.dependencies import get_audit_event_handler, get_service_session_repository
from app.api.schemas.service_session_schemas import (
    ServiceSessionCancelRequest,
    ServiceSessionCompleteRequest,
    ServiceSessionCreate,
    ServiceSessionListResponse,
    ServiceSessionRescheduleRequest,
    ServiceSessionResponse,
    ServiceSessionUpdate,
    ServiceSessionUpdateFeedback,
)
from app.application.use_cases.service_session_use_cases import (
    ArchiveServiceSessionUseCase,
    CancelServiceSessionUseCase,
    CompleteServiceSessionUseCase,
    CreateServiceSessionUseCase,
    GetServiceSessionUseCase,
    MarkNoShowServiceSessionUseCase,
    RescheduleServiceSessionUseCase,
    RestoreServiceSessionUseCase,
    UpdateServiceSessionFeedbackUseCase,
    UpdateServiceSessionUseCase,
)
from app.core.database import get_db
from app.domain.enums import SessionStatus
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.repositories.service_session_repository import (
    ServiceSessionRepository,
)
from app.domain.value_objects.core import (
    PersonId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/service-sessions", tags=["service-sessions"])


def _to_service_session_response(
    session: ServiceSessionEntity,
) -> ServiceSessionResponse:
    """Map ServiceSessionEntity to API response using public properties."""
    return ServiceSessionResponse(
        id=session.id.value,
        tenant_id=session.tenant_id.value,
        service_id=session.service_id.value,
        provider_id=session.provider_id.value,
        person_id=session.person_id.value,
        scheduled_at=session.scheduled_at,
        status=session.status,
        reschedule_count=session.reschedule_count,
        completed_at=session.completed_at,
        duration=session.duration,
        location=session.location,
        notes=session.notes,
        feedback=session.feedback,
        cancellation_reason=session.cancellation_reason,
        is_active=session.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ServiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service session",
)
@transactional()
async def create_service_session(
    data: ServiceSessionCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service session."""
    session = await CreateServiceSessionUseCase(session_repo).execute(
        session_id=SessionId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        service_id=ServiceId(data.service_id),
        provider_id=PersonId(data.provider_id),
        person_id=PersonId(data.person_id),
        scheduled_at=data.scheduled_at,
        location=data.location,
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.post(
    "/{session_id}/complete",
    response_model=ServiceSessionResponse,
    summary="Complete a service session",
)
@transactional()
async def complete_service_session(
    request: Request,
    body: ServiceSessionCompleteRequest,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Complete a service session."""
    session = await CompleteServiceSessionUseCase(session_repo).execute(
        session.id, body.duration, body.notes
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.post(
    "/{session_id}/cancel",
    response_model=ServiceSessionResponse,
    summary="Cancel a service session",
)
@transactional()
async def cancel_service_session(
    request: Request,
    body: ServiceSessionCancelRequest,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a service session."""
    session = await CancelServiceSessionUseCase(session_repo).execute(
        session.id, body.reason
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.post(
    "/{session_id}/reschedule",
    response_model=ServiceSessionResponse,
    summary="Reschedule a service session",
)
@transactional()
async def reschedule_service_session(
    request: Request,
    body: ServiceSessionRescheduleRequest,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Reschedule a service session."""
    session = await RescheduleServiceSessionUseCase(session_repo).execute(
        session.id, body.new_scheduled_at
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.post(
    "/{session_id}/no-show",
    response_model=ServiceSessionResponse,
    summary="Mark a service session as no-show",
)
@transactional()
async def mark_no_show_service_session(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Mark a service session as no-show."""
    session = await MarkNoShowServiceSessionUseCase(session_repo).execute(
        session.id
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.patch(
    "/{session_id}",
    response_model=ServiceSessionResponse,
    summary="Update service session information",
)
@transactional()
async def update_service_session(
    data: ServiceSessionUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update service session information."""
    session = await UpdateServiceSessionUseCase(session_repo).execute(
        session.id, location=data.location, notes=data.notes
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.patch(
    "/{session_id}/feedback",
    response_model=ServiceSessionResponse,
    summary="Update service session feedback",
)
@transactional()
async def update_service_session_feedback(
    request: Request,
    body: ServiceSessionUpdateFeedback,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update service session feedback."""
    session = await UpdateServiceSessionFeedbackUseCase(session_repo).execute(
        session.id, body.feedback
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.post(
    "/{session_id}/archive",
    response_model=ServiceSessionResponse,
    summary="Archive a service session",
)
@transactional()
async def archive_service_session(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a service session."""
    session = await ArchiveServiceSessionUseCase(session_repo).execute(
        session.id
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


@router.post(
    "/{session_id}/restore",
    response_model=ServiceSessionResponse,
    summary="Restore a service session",
)
@transactional()
async def restore_service_session(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived service session."""
    session = await RestoreServiceSessionUseCase(session_repo).execute(
        session.id
    )
    await audit_entity_operation(
        entity=session,
        audit_handler=audit_handler,
        tenant_id=session.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_session_response(session)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=ServiceSessionListResponse,
    summary="List service sessions with filtering and pagination",
)
@readonly()
async def list_service_sessions(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    person_id: str | None = Query(None, description="Filter by person identifier"),
    provider_id: str | None = Query(None, description="Filter by provider identifier"),
    service_id: str | None = Query(None, description="Filter by service identifier"),
    status: SessionStatus | None = Query(None, description="Filter by session status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("scheduled_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """List service sessions with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    sessions = await session_repo.list_all(
        tenant_id=TenantId(tenant_id),
        person_id=PersonId(person_id) if person_id else None,
        provider_id=PersonId(provider_id) if provider_id else None,
        service_id=ServiceId(service_id) if service_id else None,
        status=status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await session_repo.count(
        tenant_id=TenantId(tenant_id),
        person_id=PersonId(person_id) if person_id else None,
        provider_id=PersonId(provider_id) if provider_id else None,
        service_id=ServiceId(service_id) if service_id else None,
        status=status,
    )

    return ServiceSessionListResponse(
        items=[_to_service_session_response(session) for session in sessions],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{session_id}",
    response_model=ServiceSessionResponse,
    summary="Get service session by ID",
)
@readonly()
async def get_service_session(
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get service session by ID."""
    return _to_service_session_response(session)


@router.get(
    "/person/{person_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a person",
)
@readonly()
async def get_sessions_by_person(
    person_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all sessions for a person."""
    sessions = await GetServiceSessionUseCase(session_repo).execute_by_person(
        TenantId(tenant_id), PersonId(person_id)
    )
    return [_to_service_session_response(session) for session in sessions]


@router.get(
    "/provider/{provider_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a provider",
)
@readonly()
async def get_sessions_by_provider(
    provider_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all sessions for a provider."""
    sessions = await GetServiceSessionUseCase(session_repo).execute_by_provider(
        TenantId(tenant_id), PersonId(provider_id)
    )
    return [_to_service_session_response(session) for session in sessions]


@router.get(
    "/service/{service_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a service",
)
@readonly()
async def get_sessions_by_service(
    service_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all sessions for a service."""
    sessions = await GetServiceSessionUseCase(session_repo).execute_by_service(
        TenantId(tenant_id), ServiceId(service_id)
    )
    return [_to_service_session_response(session) for session in sessions]
