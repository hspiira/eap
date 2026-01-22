"""
Service API Routes

FastAPI routes for Service operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_service_repository
from app.api.schemas.service_schemas import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
    ServiceUpdate,
    ServiceUpdateGroupSettings,
)
from app.application.use_cases.service_use_cases import (
    ActivateServiceUseCase,
    ArchiveServiceUseCase,
    CreateServiceUseCase,
    DeactivateServiceUseCase,
    GetServiceUseCase,
    RestoreServiceUseCase,
    UpdateServiceGroupSettingsUseCase,
    UpdateServiceUseCase,
)
from app.core.database import get_db
from app.domain.enums import BaseStatus
from app.domain.entities.service import ServiceEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.value_objects.core import ServiceId, TenantId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/services", tags=["services"])


def _to_service_response(service: ServiceEntity) -> ServiceResponse:
    """Map ServiceEntity to API response."""
    return ServiceResponse(
        id=service._id.value,
        tenant_id=service._tenant_id.value,
        name=service._name,
        description=service._description,
        category=service._category,
        status=service._status,
        duration_minutes=service._duration_minutes,
        is_group_service=service._is_group_service,
        max_participants=service._max_participants,
        is_active=service.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service",
)
async def create_service(
    data: ServiceCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new service.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_use_case = CreateServiceUseCase(service_repo)

        service = await create_use_case.execute(
            service_id=ServiceId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            name=data.name,
            description=data.description,
            category=data.category,
            duration_minutes=data.duration_minutes,
            is_group_service=data.is_group_service,
            max_participants=data.max_participants,
        )

        await db.commit()

        return _to_service_response(service)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{service_id}/activate",
    response_model=ServiceResponse,
    summary="Activate a service",
)
async def activate_service(
    service_id: str,
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a service.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateServiceUseCase(service_repo)

        service = await activate_use_case.execute(ServiceId(service_id))

        await db.commit()

        return _to_service_response(service)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{service_id}/deactivate",
    response_model=ServiceResponse,
    summary="Deactivate a service",
)
async def deactivate_service(
    service_id: str,
    reason: str | None = Query(None, description="Deactivation reason"),
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a service.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        deactivate_use_case = DeactivateServiceUseCase(service_repo)

        service = await deactivate_use_case.execute(ServiceId(service_id), reason)

        await db.commit()

        return _to_service_response(service)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{service_id}/archive",
    response_model=ServiceResponse,
    summary="Archive a service",
)
async def archive_service(
    service_id: str,
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a service.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        archive_use_case = ArchiveServiceUseCase(service_repo)

        service = await archive_use_case.execute(ServiceId(service_id))

        await db.commit()

        return _to_service_response(service)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{service_id}/restore",
    response_model=ServiceResponse,
    summary="Restore a service",
)
async def restore_service(
    service_id: str,
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore an archived or soft-deleted service.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        restore_use_case = RestoreServiceUseCase(service_repo)

        service = await restore_use_case.execute(ServiceId(service_id))

        await db.commit()

        return _to_service_response(service)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update service information",
)
async def update_service(
    service_id: str,
    data: ServiceUpdate,
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update service information.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateServiceUseCase(service_repo)

        service = await update_use_case.execute(
            ServiceId(service_id),
            name=data.name,
            description=data.description,
            category=data.category,
            duration_minutes=data.duration_minutes,
        )

        await db.commit()

        return _to_service_response(service)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{service_id}/group-settings",
    response_model=ServiceResponse,
    summary="Update service group settings",
)
async def update_service_group_settings(
    service_id: str,
    request: ServiceUpdateGroupSettings,
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update service group settings.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateServiceGroupSettingsUseCase(service_repo)

        service = await update_use_case.execute(
            ServiceId(service_id),
            is_group_service=request.is_group_service,
            max_participants=request.max_participants,
        )

        await db.commit()

        return _to_service_response(service)
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
    response_model=ServiceListResponse,
    summary="List services with filtering and pagination",
)
async def list_services(
    tenant_id: str = Query(..., description="Tenant identifier"),
    status: BaseStatus | None = Query(None, description="Filter by service status"),
    category: str | None = Query(None, description="Filter by service category"),
    is_group_service: bool | None = Query(None, description="Filter by group service flag"),
    search: str | None = Query(None, description="Search in name or description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    service_repo: ServiceRepository = Depends(get_service_repository),
):
    """
    List services with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
    offset = (page - 1) * limit

    services = await service_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        category=category,
        is_group_service=is_group_service,
        search=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await service_repo.count(
        tenant_id=TenantId(tenant_id),
        status=status,
        category=category,
        is_group_service=is_group_service,
        search=search,
    )

    service_responses = [_to_service_response(service) for service in services]

    return ServiceListResponse(
        items=service_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get service by ID",
)
async def get_service(
    service_id: str,
    service_repo: ServiceRepository = Depends(get_service_repository),
):
    """
    Get service by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    service = await service_repo.get_by_id(ServiceId(service_id))

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )

    return _to_service_response(service)


@router.get(
    "/name/{name}",
    response_model=ServiceResponse,
    summary="Get service by name",
)
async def get_service_by_name(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    service_repo: ServiceRepository = Depends(get_service_repository),
):
    """
    Get service by name within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    service = await service_repo.get_by_name(TenantId(tenant_id), name)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )

    return _to_service_response(service)


@router.get(
    "/check-name/{name}",
    summary="Check if service name is available",
)
async def check_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    service_repo: ServiceRepository = Depends(get_service_repository),
):
    """
    Check if a service name is available within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    service = await service_repo.get_by_name(TenantId(tenant_id), name)
    return {"available": service is None, "name": name, "tenant_id": tenant_id}
