"""
Tenant API Routes

FastAPI routes for Tenant operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import (
    require_platform_admin_if_configured,
    require_same_tenant,
    require_tenant_role,
)
from app.core.security import TokenData, get_current_user
from app.domain.enums import TenantRole

from app.api.dependencies import (
    get_audit_event_handler,
    get_client_repository,
    get_industry_repository,
    get_password_set_token_repository,
    get_tenant_repository,
    get_user_repository,
)
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.industry_repository import IndustryRepository
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
from app.core.config import settings
from app.core.database import get_db
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.entities.tenant import TenantEntity
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantId
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.repositories.password_set_token_repository import (
    PasswordSetTokenRepository,
)
from app.infrastructure.models.user_model import UserModel
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _to_tenant_response(
    tenant: TenantEntity,
    admin_email: str | None = None,
    admin_password: str | None = None,
    set_password_url: str | None = None,
    set_password_expires_at=None,
) -> TenantResponse:
    """
    Map TenantEntity to API response using public properties.

    Args:
        tenant: Tenant entity
        admin_email: Admin email (on creation)
        admin_password: Admin password (only when set-password flow not used)
        set_password_url: URL for set-password page (when SET_PASSWORD_BASE_URL is set)
        set_password_expires_at: When set-password link expires
    """
    return TenantResponse(
        id=tenant.id.value,
        name=tenant.name,
        code=tenant.code.value,
        status=tenant.status,
        subscription_tier=tenant.subscription_tier,
        settings=TenantSettingsResponse(
            max_users=tenant.settings.max_users,
            max_clients=tenant.settings.max_clients,
            features_enabled=list(tenant.settings.features_enabled),
            custom_branding=tenant.settings.custom_branding,
        ),
        is_active=tenant.is_active(),
        admin_email=admin_email,
        admin_password=admin_password,
        set_password_url=set_password_url,
        set_password_expires_at=set_password_expires_at,
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
)
@transactional()
async def create_tenant(
    data: TenantCreate,
    request: Request,
    _tenant_creation_auth: None = Depends(require_platform_admin_if_configured),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    password_set_token_repo: PasswordSetTokenRepository
    | None = Depends(get_password_set_token_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tenant, seed default industries, and create an admin user.

    When SET_PASSWORD_BASE_URL is set, the response includes set_password_url
    (and set_password_expires_at). The admin must open that link to set a
    password, then log in with tenant code, that email, and the new password.
    Otherwise the response includes a one-time admin_password.
    """
    token_repo = (
        password_set_token_repo
        if getattr(settings, "SET_PASSWORD_BASE_URL", "")
        else None
    )
    tenant, admin_email, admin_password, set_password_token, set_password_expires_at = (
        await CreateTenantUseCase(
            tenant_repo,
            user_repo,
            industry_repo,
            password_set_token_repository=token_repo,
        ).execute(
            tenant_id=TenantId(generate_cuid()),
            name=data.name,
            code=data.code,
            subscription_tier=data.subscription_tier,
            max_users=data.settings.max_users,
            max_clients=data.settings.max_clients,
            features_enabled=tuple(data.settings.features_enabled),
            custom_branding=data.settings.custom_branding,
        )
    )
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=None,
        request=request,
    )
    set_password_url = None
    if set_password_token and getattr(settings, "SET_PASSWORD_BASE_URL", ""):
        base = settings.SET_PASSWORD_BASE_URL.rstrip("/")
        set_password_url = f"{base}/set-password?token={set_password_token}"
    return _to_tenant_response(
        tenant,
        admin_email=admin_email,
        admin_password=admin_password,
        set_password_url=set_password_url,
        set_password_expires_at=set_password_expires_at,
    )


@router.post(
    "/{tenant_id}/activate",
    response_model=TenantResponse,
    summary="Activate a tenant",
)
@transactional()
async def activate_tenant(
    tenant_id: str,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a tenant."""
    tenant = await ActivateTenantUseCase(tenant_repo).execute(TenantId(tenant_id))
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


@router.post(
    "/{tenant_id}/suspend",
    response_model=TenantResponse,
    summary="Suspend a tenant",
)
@transactional()
async def suspend_tenant(
    tenant_id: str,
    request: Request,
    body: TenantSuspendRequest,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a tenant."""
    tenant = await SuspendTenantUseCase(tenant_repo).execute(
        TenantId(tenant_id), body.reason
    )
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


@router.post(
    "/{tenant_id}/terminate",
    response_model=TenantResponse,
    summary="Terminate a tenant",
)
@transactional()
async def terminate_tenant(
    tenant_id: str,
    request: Request,
    body: TenantTerminateRequest,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a tenant."""
    tenant = await TerminateTenantUseCase(tenant_repo).execute(
        TenantId(tenant_id), body.reason
    )
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


@router.patch(
    "/{tenant_id}/settings",
    response_model=TenantResponse,
    summary="Update tenant settings",
)
@transactional()
async def update_tenant_settings(
    tenant_id: str,
    settings: TenantUpdateSettings,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant settings."""
    tenant = await UpdateTenantSettingsUseCase(tenant_repo).execute(
        TenantId(tenant_id),
        max_users=settings.max_users,
        max_clients=settings.max_clients,
        features_enabled=tuple(settings.features_enabled)
        if settings.features_enabled is not None
        else None,
        custom_branding=settings.custom_branding,
    )
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant basic information",
)
@transactional()
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant basic information."""
    tenant = await UpdateTenantUseCase(tenant_repo).execute(
        TenantId(tenant_id),
        name=data.name,
    )
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


@router.post(
    "/{tenant_id}/subscription",
    response_model=TenantResponse,
    summary="Update tenant subscription tier",
)
@transactional()
async def update_subscription(
    tenant_id: str,
    data: SubscriptionUpdateRequest,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant subscription tier."""
    tenant = await UpdateSubscriptionUseCase(tenant_repo).execute(
        TenantId(tenant_id),
        data.subscription_tier,
    )
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


@router.post(
    "/{tenant_id}/archive",
    response_model=TenantResponse,
    summary="Archive a tenant",
)
@transactional()
async def archive_tenant(
    tenant_id: str,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a tenant."""
    tenant = await ArchiveTenantUseCase(tenant_repo).execute(TenantId(tenant_id))
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


@router.post(
    "/{tenant_id}/restore",
    response_model=TenantResponse,
    summary="Restore a tenant",
)
@transactional()
async def restore_tenant(
    tenant_id: str,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived or soft-deleted tenant."""
    tenant = await RestoreTenantUseCase(tenant_repo).execute(TenantId(tenant_id))
    await audit_entity_operation(
        entity=tenant,
        audit_handler=audit_handler,
        tenant_id=tenant.id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_tenant_response(tenant)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=TenantListResponse,
    summary="List tenants with filtering and pagination",
)
@readonly()
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
    db: AsyncSession = Depends(get_db),
):
    """List tenants with filtering, searching, and pagination."""
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

    return TenantListResponse(
        items=[_to_tenant_response(tenant) for tenant in tenants],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/check-code/{code}",
    summary="Check if tenant code is available",
)
@readonly()
async def check_code_availability(
    code: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a tenant code is available."""
    tenant = await tenant_repo.get_by_code(code)
    return {"available": tenant is None, "code": code}


@router.get(
    "/{tenant_id}/stats",
    response_model=TenantStatsResponse,
    summary="Get tenant statistics",
)
@readonly()
async def get_tenant_stats(
    tenant_id: str,
    current_user: TokenData = Depends(require_same_tenant),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant statistics including user and client counts."""
    tenant = await tenant_repo.get_by_id(TenantId(tenant_id))
    if not tenant:
        raise ValueError("Tenant not found")
    user_count = await user_repo.count(tenant_id=TenantId(tenant_id))
    client_count = await client_repo.count(tenant_id=TenantId(tenant_id)) 

    # Calculate quota usage
    user_quota_usage = (
        (user_count / tenant.settings.max_users * 100)
        if tenant.settings.max_users > 0
        else 0.0
    )
    client_quota_usage = (
        (client_count / tenant.settings.max_clients * 100)
        if tenant.settings.max_clients > 0
        else 0.0
    )

    return TenantStatsResponse(
        tenant_id=tenant_id,
        current_user_count=user_count,
        current_client_count=client_count,
        max_users=tenant.settings.max_users,
        max_clients=tenant.settings.max_clients,
        user_quota_usage=round(user_quota_usage, 2),
        client_quota_usage=round(client_quota_usage, 2),
        subscription_tier=tenant.subscription_tier,
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID",
)
@readonly()
async def get_tenant(
    tenant_id: str,
    current_user: TokenData = Depends(require_same_tenant),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant by ID."""
    tenant = await tenant_repo.get_by_id(TenantId(tenant_id))
    if not tenant:
        raise ValueError("Tenant not found")
    return _to_tenant_response(tenant)


@router.get(
    "/code/{code}",
    response_model=TenantResponse,
    summary="Get tenant by code",
)
@readonly()
async def get_tenant_by_code(
    code: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant by code."""
    tenant = await tenant_repo.get_by_code(code)
    if not tenant:
        raise ValueError("Tenant not found")
    return _to_tenant_response(tenant)
