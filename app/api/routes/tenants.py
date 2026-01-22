"""
Tenant API Routes

FastAPI routes for Tenant operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_tenant_repository
from app.api.schemas.tenant_schemas import (
    TenantCreate,
    TenantResponse,
    TenantSettingsResponse,
    TenantSuspendRequest,
    TenantTerminateRequest,
    TenantUpdateSettings,
)
from app.application.use_cases.tenant_use_cases import (
    ActivateTenantUseCase,
    CreateTenantUseCase,
    SuspendTenantUseCase,
    TerminateTenantUseCase,
    UpdateTenantSettingsUseCase,
)
from app.core.database import get_db
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.exceptions import DomainError
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantCode, TenantId
from app.shared.utils.generators import generate_cuid

router = APIRouter(prefix="/tenants", tags=["tenants"])


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
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DomainError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DomainError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DomainError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DomainError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== QUERIES (Direct Repository) ====================


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
