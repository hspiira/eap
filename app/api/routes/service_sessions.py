"""
Service Session API Routes

FastAPI routes for Service Session operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_service_session_repository
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
from app.domain.exceptions import DomainError
from app.domain.repositories.service_session_repository import (
    ServiceSessionRepository,
)
from app.domain.value_objects.core import (
    PersonId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/service-sessions", tags=["service-sessions"])


def _to_service_session_response(
    session: ServiceSessionEntity,
) -> ServiceSessionResponse:
    """Map ServiceSessionEntity to API response."""
    return ServiceSessionResponse(
        id=session._id.value,
        tenant_id=session._tenant_id.value,
        service_id=session._service_id.value,
        provider_id=session._provider_id.value,
        person_id=session._person_id.value,
        scheduled_at=session._scheduled_at,
        status=session._status,
        reschedule_count=session._reschedule_count,
        completed_at=session._completed_at,
        duration=session._duration,
        location=session._location,
        notes=session._notes,
        feedback=session._feedback,
        cancellation_reason=session._cancellation_reason,
        is_active=session.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ServiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service session",
)
async def create_service_session(
    data: ServiceSessionCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new service session.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_use_case = CreateServiceSessionUseCase(session_repo)

        session = await create_use_case.execute(
            session_id=SessionId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            service_id=ServiceId(data.service_id),
            provider_id=PersonId(data.provider_id),
            person_id=PersonId(data.person_id),
            scheduled_at=data.scheduled_at,
            location=data.location,
        )

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{session_id}/complete",
    response_model=ServiceSessionResponse,
    summary="Complete a service session",
)
async def complete_service_session(
    session_id: str,
    request: ServiceSessionCompleteRequest,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete a service session.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        complete_use_case = CompleteServiceSessionUseCase(session_repo)

        session = await complete_use_case.execute(
            SessionId(session_id), request.duration, request.notes
        )

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{session_id}/cancel",
    response_model=ServiceSessionResponse,
    summary="Cancel a service session",
)
async def cancel_service_session(
    session_id: str,
    request: ServiceSessionCancelRequest,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a service session.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        cancel_use_case = CancelServiceSessionUseCase(session_repo)

        session = await cancel_use_case.execute(SessionId(session_id), request.reason)

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{session_id}/reschedule",
    response_model=ServiceSessionResponse,
    summary="Reschedule a service session",
)
async def reschedule_service_session(
    session_id: str,
    request: ServiceSessionRescheduleRequest,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Reschedule a service session.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        reschedule_use_case = RescheduleServiceSessionUseCase(session_repo)

        session = await reschedule_use_case.execute(
            SessionId(session_id), request.new_scheduled_at
        )

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{session_id}/no-show",
    response_model=ServiceSessionResponse,
    summary="Mark a service session as no-show",
)
async def mark_no_show_service_session(
    session_id: str,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a service session as no-show.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        mark_no_show_use_case = MarkNoShowServiceSessionUseCase(session_repo)

        session = await mark_no_show_use_case.execute(SessionId(session_id))

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{session_id}",
    response_model=ServiceSessionResponse,
    summary="Update service session information",
)
async def update_service_session(
    session_id: str,
    data: ServiceSessionUpdate,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update service session information.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateServiceSessionUseCase(session_repo)

        session = await update_use_case.execute(
            SessionId(session_id), location=data.location, notes=data.notes
        )

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{session_id}/feedback",
    response_model=ServiceSessionResponse,
    summary="Update service session feedback",
)
async def update_service_session_feedback(
    session_id: str,
    request: ServiceSessionUpdateFeedback,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update service session feedback.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateServiceSessionFeedbackUseCase(session_repo)

        session = await update_use_case.execute(
            SessionId(session_id), request.feedback
        )

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{session_id}/archive",
    response_model=ServiceSessionResponse,
    summary="Archive a service session",
)
async def archive_service_session(
    session_id: str,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a service session.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        archive_use_case = ArchiveServiceSessionUseCase(session_repo)

        session = await archive_use_case.execute(SessionId(session_id))

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{session_id}/restore",
    response_model=ServiceSessionResponse,
    summary="Restore a service session",
)
async def restore_service_session(
    session_id: str,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore an archived service session.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        restore_use_case = RestoreServiceSessionUseCase(session_repo)

        session = await restore_use_case.execute(SessionId(session_id))

        await db.commit()

        return _to_service_session_response(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=ServiceSessionListResponse,
    summary="List service sessions with filtering and pagination",
)
async def list_service_sessions(
    tenant_id: str = Query(..., description="Tenant identifier"),
    person_id: str | None = Query(None, description="Filter by person identifier"),
    provider_id: str | None = Query(None, description="Filter by provider identifier"),
    service_id: str | None = Query(None, description="Filter by service identifier"),
    status: SessionStatus | None = Query(None, description="Filter by session status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("scheduled_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
):
    """
    List service sessions with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
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

    session_responses = [
        _to_service_session_response(session) for session in sessions
    ]

    return ServiceSessionListResponse(
        items=session_responses,
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
async def get_service_session(
    session_id: str,
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
):
    """
    Get service session by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    session = await session_repo.get_by_id(SessionId(session_id))

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service session not found"
        )

    return _to_service_session_response(session)


@router.get(
    "/person/{person_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a person",
)
async def get_sessions_by_person(
    person_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
):
    """
    Get all sessions for a person.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetServiceSessionUseCase(session_repo)

    sessions = await get_use_case.execute_by_person(
        TenantId(tenant_id), PersonId(person_id)
    )

    return [_to_service_session_response(session) for session in sessions]


@router.get(
    "/provider/{provider_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a provider",
)
async def get_sessions_by_provider(
    provider_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
):
    """
    Get all sessions for a provider.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetServiceSessionUseCase(session_repo)

    sessions = await get_use_case.execute_by_provider(
        TenantId(tenant_id), PersonId(provider_id)
    )

    return [_to_service_session_response(session) for session in sessions]


@router.get(
    "/service/{service_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a service",
)
async def get_sessions_by_service(
    service_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
):
    """
    Get all sessions for a service.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetServiceSessionUseCase(session_repo)

    sessions = await get_use_case.execute_by_service(
        TenantId(tenant_id), ServiceId(service_id)
    )

    return [_to_service_session_response(session) for session in sessions]
