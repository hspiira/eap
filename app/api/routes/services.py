"""
Service API Routes

FastAPI routes for Service operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import (
    get_service_for_current_tenant,
    require_same_tenant,
)
from app.core.security import TokenData, get_current_user

from app.api.dependencies import get_audit_event_handler, get_service_repository
from app.api.schemas.service_schemas import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
    ServiceUpdate,
    ServiceUpdateGroupSettings,
)
from app.application.use_cases.service_use_cases import (
    CreateServiceUseCase,
    UpdateServiceGroupSettingsUseCase,
    UpdateServiceUseCase,
)
from app.application.use_cases.transitions import (
    ServiceTransition,
    TransitionUseCase,
)
from app.core.database import get_db
from app.domain.enums import BaseStatus
from app.domain.entities.service import ServiceEntity
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.value_objects.core import ServiceId, TenantId
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/services", tags=["services"])


def _to_service_response(service: ServiceEntity) -> ServiceResponse:
    """Map ServiceEntity to API response using public properties."""
    return ServiceResponse(
        id=service.id.value,
        tenant_id=service.tenant_id.value,
        name=service.name,
        description=service.description,
        category=service.category,
        status=service.status,
        duration_minutes=service.duration_minutes,
        is_group_service=service.is_group_service,
        max_participants=service.max_participants,
        is_active=service.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service",
)
@transactional()
async def create_service(
    data: ServiceCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service."""
    service = await CreateServiceUseCase(service_repo).execute(
        service_id=ServiceId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        name=data.name,
        description=data.description,
        category=data.category,
        duration_minutes=data.duration_minutes,
        is_group_service=data.is_group_service,
        max_participants=data.max_participants,
    )
    await audit_entity_operation(
        entity=service,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_response(service)


@router.post(
    "/{service_id}/activate",
    response_model=ServiceResponse,
    summary="Activate a service",
)
@transactional()
async def activate_service(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    service: ServiceEntity = Depends(get_service_for_current_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a service."""
    use_case: TransitionUseCase = TransitionUseCase(service_repo)
    use_case.entity_name = "Service"
    service = await use_case.execute(service.id, ServiceTransition.ACTIVATE)
    await audit_entity_operation(
        entity=service,
        audit_handler=audit_handler,
        tenant_id=service.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_response(service)


@router.post(
    "/{service_id}/deactivate",
    response_model=ServiceResponse,
    summary="Deactivate a service",
)
@transactional()
async def deactivate_service(
    request: Request,
    reason: str | None = Query(None, description="Deactivation reason"),
    current_user: TokenData = Depends(get_current_user),
    service: ServiceEntity = Depends(get_service_for_current_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a service."""
    use_case: TransitionUseCase = TransitionUseCase(service_repo)
    use_case.entity_name = "Service"
    service = await use_case.execute(
        service.id, ServiceTransition.DEACTIVATE, reason=reason
    )
    await audit_entity_operation(
        entity=service,
        audit_handler=audit_handler,
        tenant_id=service.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_response(service)


@router.post(
    "/{service_id}/archive",
    response_model=ServiceResponse,
    summary="Archive a service",
)
@transactional()
async def archive_service(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    service: ServiceEntity = Depends(get_service_for_current_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a service."""
    use_case: TransitionUseCase = TransitionUseCase(service_repo)
    use_case.entity_name = "Service"
    service = await use_case.execute(service.id, ServiceTransition.ARCHIVE)
    await audit_entity_operation(
        entity=service,
        audit_handler=audit_handler,
        tenant_id=service.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_response(service)


@router.post(
    "/{service_id}/restore",
    response_model=ServiceResponse,
    summary="Restore a service",
)
@transactional()
async def restore_service(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    service: ServiceEntity = Depends(get_service_for_current_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived or soft-deleted service."""
    use_case: TransitionUseCase = TransitionUseCase(service_repo)
    use_case.entity_name = "Service"
    service = await use_case.execute(service.id, ServiceTransition.RESTORE)
    await audit_entity_operation(
        entity=service,
        audit_handler=audit_handler,
        tenant_id=service.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_response(service)


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update service basic information",
)
@transactional()
async def update_service(
    data: ServiceUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    service: ServiceEntity = Depends(get_service_for_current_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update service basic information."""
    service = await UpdateServiceUseCase(service_repo).execute(
        service.id,
        name=data.name,
        description=data.description,
        category=data.category,
        duration_minutes=data.duration_minutes,
    )
    await audit_entity_operation(
        entity=service,
        audit_handler=audit_handler,
        tenant_id=service.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_response(service)


@router.patch(
    "/{service_id}/group-settings",
    response_model=ServiceResponse,
    summary="Update service group settings",
)
@transactional()
async def update_service_group_settings(
    settings: ServiceUpdateGroupSettings,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    service: ServiceEntity = Depends(get_service_for_current_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update service group settings."""
    service = await UpdateServiceGroupSettingsUseCase(service_repo).execute(
        service.id,
        is_group_service=settings.is_group_service,
        max_participants=settings.max_participants,
    )
    await audit_entity_operation(
        entity=service,
        audit_handler=audit_handler,
        tenant_id=service.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_response(service)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=ServiceListResponse,
    summary="List services with filtering and pagination",
)
@readonly()
async def list_services(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    status: BaseStatus | None = Query(None, description="Filter by service status"),
    search: str | None = Query(None, description="Search in service name"),
    category: str | None = Query(None, description="Filter by category"),
    is_group_service: bool | None = Query(None, description="Filter by group service"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """List services with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    services = await service_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        search=search,
        category=category,
        is_group_service=is_group_service,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await service_repo.count(
        tenant_id=TenantId(tenant_id),
        status=status,
        search=search,
        category=category,
        is_group_service=is_group_service,
    )

    return ServiceListResponse(
        items=[_to_service_response(service) for service in services],
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
@readonly()
async def get_service(
    service: ServiceEntity = Depends(get_service_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get service by ID."""
    return _to_service_response(service)


@router.get(
    "/name/{name}",
    response_model=ServiceResponse,
    summary="Get service by name",
)
@readonly()
async def get_service_by_name(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get service by name within a tenant."""
    service = await service_repo.get_by_name(TenantId(tenant_id), name)
    if not service:
        raise ValueError("Service not found")
    return _to_service_response(service)


@router.get(
    "/check-name/{name}",
    summary="Check if service name is available",
)
@readonly()
async def check_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    service_repo: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a service name is available within a tenant."""
    service = await service_repo.get_by_name(TenantId(tenant_id), name)
    return {"available": service is None, "name": name, "tenant_id": tenant_id}
