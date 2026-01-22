"""
Tenant API Routes

FastAPI routes for Tenant operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_client_repository,
    get_tenant_repository,
    get_user_repository,
)
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.user_repository import UserRepository
from app.api.schemas.tenant_schemas import (
    SubscriptionUpdateRequest,
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantSettingsResponse,
    TenantStatsResponse,
    TenantSuspendRequest,
    TenantTerminateRequest,
    TenantUpdate,
    TenantUpdateSettings,
)
from app.application.use_cases.tenant_use_cases import (
    ActivateTenantUseCase,
    ArchiveTenantUseCase,
    CreateTenantUseCase,
    RestoreTenantUseCase,
    SuspendTenantUseCase,
    TerminateTenantUseCase,
    UpdateSubscriptionUseCase,
    UpdateTenantSettingsUseCase,
    UpdateTenantUseCase,
)
from app.core.database import get_db
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.exceptions import DomainError
from app.domain.entities.tenant import TenantEntity
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantId
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.user_model import UserModel
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _to_tenant_response(tenant: TenantEntity) -> TenantResponse:
    """Map TenantEntity to API response."""
    return TenantResponse(
        id=tenant._id.value,
        name=tenant._name,
        code=tenant._code.value,
        status=tenant._status,
        subscription_tier=tenant._subscription_tier,
        settings=TenantSettingsResponse(
            max_users=tenant._settings.max_users,
            max_clients=tenant._settings.max_clients,
            features_enabled=list(tenant._settings.features_enabled),
            custom_branding=tenant._settings.custom_branding,
        ),
        is_active=tenant.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
)
async def create_tenant(
    data: TenantCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tenant.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_use_case = CreateTenantUseCase(tenant_repo)

        tenant = await create_use_case.execute(
            tenant_id=TenantId(generate_cuid()),
            name=data.name,
            code=data.code,
            subscription_tier=data.subscription_tier,
            max_users=data.settings.max_users,
            max_clients=data.settings.max_clients,
            features_enabled=tuple(data.settings.features_enabled),
            custom_branding=data.settings.custom_branding,
        )

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tenant_id}/activate",
    response_model=TenantResponse,
    summary="Activate a tenant",
)
async def activate_tenant(
    tenant_id: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a tenant.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateTenantUseCase(tenant_repo)

        tenant = await activate_use_case.execute(TenantId(tenant_id))

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tenant_id}/suspend",
    response_model=TenantResponse,
    summary="Suspend a tenant",
)
async def suspend_tenant(
    tenant_id: str,
    request: TenantSuspendRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Suspend a tenant.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        suspend_use_case = SuspendTenantUseCase(tenant_repo)

        tenant = await suspend_use_case.execute(
            TenantId(tenant_id), request.reason
        )

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tenant_id}/terminate",
    response_model=TenantResponse,
    summary="Terminate a tenant",
)
async def terminate_tenant(
    tenant_id: str,
    request: TenantTerminateRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Terminate a tenant.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        terminate_use_case = TerminateTenantUseCase(tenant_repo)

        tenant = await terminate_use_case.execute(
            TenantId(tenant_id), request.reason
        )

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{tenant_id}/settings",
    response_model=TenantResponse,
    summary="Update tenant settings",
)
async def update_tenant_settings(
    tenant_id: str,
    settings: TenantUpdateSettings,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update tenant settings.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateTenantSettingsUseCase(tenant_repo)

        tenant = await update_use_case.execute(
            TenantId(tenant_id),
            max_users=settings.max_users,
            max_clients=settings.max_clients,
            features_enabled=tuple(settings.features_enabled)
            if settings.features_enabled is not None
            else None,
            custom_branding=settings.custom_branding,
        )

        await db.commit()

        return _to_tenant_response(tenant)
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
    response_model=TenantListResponse,
    summary="List tenants with filtering and pagination",
)
async def list_tenants(
    status: TenantStatus | None = Query(None, description="Filter by tenant status"),
    subscription_tier: SubscriptionTier | None = Query(
        None, description="Filter by subscription tier"
    ),
    search: str | None = Query(None, description="Search in name or code"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """
    List tenants with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
    offset = (page - 1) * limit

    tenants = await tenant_repo.list_all(
        status=status,
        subscription_tier=subscription_tier,
        search=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await tenant_repo.count(
        status=status,
        subscription_tier=subscription_tier,
        search=search,
    )

    tenant_responses = [_to_tenant_response(tenant) for tenant in tenants]

    return TenantListResponse(
        items=tenant_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/check-code/{code}",
    summary="Check if tenant code is available",
)
async def check_code_availability(
    code: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """
    Check if a tenant code is available.

    This is a QUERY operation, so it calls the repository directly.
    """
    tenant = await tenant_repo.get_by_code(code)
    return {"available": tenant is None, "code": code}


@router.get(
    "/{tenant_id}/stats",
    response_model=TenantStatsResponse,
    summary="Get tenant statistics",
)
async def get_tenant_stats(
    tenant_id: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tenant statistics including user and client counts.

    This is a QUERY operation that aggregates data from multiple repositories.
    """
    tenant = await tenant_repo.get_by_id(TenantId(tenant_id))

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    # Count users for this tenant
    user_count_stmt = select(func.count(UserModel.id)).where(
        UserModel.tenant_id == tenant_id,
        UserModel.deleted_at.is_(None),
    )
    user_result = await db.execute(user_count_stmt)
    user_count = int(user_result.scalar() or 0)

    # Count clients for this tenant
    client_count_stmt = select(func.count(ClientModel.id)).where(
        ClientModel.tenant_id == tenant_id,
        ClientModel.deleted_at.is_(None),
    )
    client_result = await db.execute(client_count_stmt)
    client_count = int(client_result.scalar() or 0)

    # Calculate quota usage
    user_quota_usage = (
        (user_count / tenant._settings.max_users * 100)
        if tenant._settings.max_users > 0
        else 0.0
    )
    client_quota_usage = (
        (client_count / tenant._settings.max_clients * 100)
        if tenant._settings.max_clients > 0
        else 0.0
    )

    return TenantStatsResponse(
        tenant_id=tenant_id,
        current_user_count=user_count,
        current_client_count=client_count,
        max_users=tenant._settings.max_users,
        max_clients=tenant._settings.max_clients,
        user_quota_usage=round(user_quota_usage, 2),
        client_quota_usage=round(client_quota_usage, 2),
        subscription_tier=tenant._subscription_tier,
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID",
)
async def get_tenant(
    tenant_id: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """
    Get tenant by ID.

    This is a QUERY operation, so it calls the repository directly.
    No use case needed for simple reads.
    """
    tenant = await tenant_repo.get_by_id(TenantId(tenant_id))

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    return _to_tenant_response(tenant)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant basic information",
)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update tenant basic information.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateTenantUseCase(tenant_repo)

        tenant = await update_use_case.execute(
            TenantId(tenant_id),
            name=data.name,
        )

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tenant_id}/subscription",
    response_model=TenantResponse,
    summary="Update tenant subscription tier",
)
async def update_subscription(
    tenant_id: str,
    data: SubscriptionUpdateRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update tenant subscription tier.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateSubscriptionUseCase(tenant_repo)

        tenant = await update_use_case.execute(
            TenantId(tenant_id),
            data.subscription_tier,
        )

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tenant_id}/archive",
    response_model=TenantResponse,
    summary="Archive a tenant",
)
async def archive_tenant(
    tenant_id: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a tenant.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        archive_use_case = ArchiveTenantUseCase(tenant_repo)

        tenant = await archive_use_case.execute(TenantId(tenant_id))

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tenant_id}/restore",
    response_model=TenantResponse,
    summary="Restore a tenant",
)
async def restore_tenant(
    tenant_id: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore an archived or soft-deleted tenant.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        restore_use_case = RestoreTenantUseCase(tenant_repo)

        tenant = await restore_use_case.execute(TenantId(tenant_id))

        await db.commit()

        return _to_tenant_response(tenant)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.get(
    "/code/{code}",
    response_model=TenantResponse,
    summary="Get tenant by code",
)
async def get_tenant_by_code(
    code: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """
    Get tenant by code.

    This is a QUERY operation, so it calls the repository directly.
    No use case needed for simple reads.
    """
    tenant = await tenant_repo.get_by_code(code)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    return _to_tenant_response(tenant)
