"""
Tenant API Routes

FastAPI routes for Tenant operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_client_repository,
    get_industry_repository,
    get_password_set_token_repository,
    get_tenant_repository,
    get_user_repository,
    pagination,
)
from app.api.schemas.tenant_schemas import (
    SubscriptionUpdateRequest,
    TenantAzureSsoRequest,
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
from app.application.use_cases.tenant_use_cases import CreateTenantUseCase
from app.application.use_cases.transitions import (
    TenantTransition,
    TransitionUseCase,
)
from app.core.authorization import (
    require_platform_admin_if_configured,
    require_same_tenant,
    require_tenant_role,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.tenant import TenantEntity
from app.domain.enums import SubscriptionTier, TenantRole, TenantStatus
from app.domain.exceptions import NotFoundError
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import TenantId
from app.infrastructure.repositories.password_set_token_repository import (
    PasswordSetTokenRepository,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

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
        azure_tenant_id=tenant.azure_tenant_id,
        azure_sso_enabled=tenant.azure_sso_enabled,
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
    password_set_token_repo: PasswordSetTokenRepository | None = Depends(
        get_password_set_token_repository
    ),
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
    token_repo = password_set_token_repo if getattr(settings, "SET_PASSWORD_BASE_URL", "") else None
    (
        tenant,
        admin_email,
        admin_password,
        set_password_token,
        set_password_expires_at,
    ) = await CreateTenantUseCase(
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
        admin_email=data.admin_email,
    )
    await audit_change(tenant, audit_handler, None, request, tenant_id=tenant.id)
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
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(TenantId(tenant_id), TenantTransition.ACTIVATE)
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
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
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(
        TenantId(tenant_id), TenantTransition.SUSPEND, reason=body.reason
    )
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
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
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(
        TenantId(tenant_id), TenantTransition.TERMINATE, reason=body.reason
    )
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
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
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(
        TenantId(tenant_id),
        TenantTransition.UPDATE_SETTINGS,
        max_users=settings.max_users,
        max_clients=settings.max_clients,
        features_enabled=tuple(settings.features_enabled)
        if settings.features_enabled is not None
        else None,
        custom_branding=settings.custom_branding,
    )
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
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
    if data.name is None:
        tenant = await tenant_repo.get_by_id(TenantId(tenant_id))
        if tenant is None:
            raise NotFoundError(f"Tenant not found: {tenant_id}")
        return _to_tenant_response(tenant)
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(
        TenantId(tenant_id), TenantTransition.UPDATE_NAME, name=data.name
    )
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
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
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(
        TenantId(tenant_id),
        TenantTransition.UPDATE_SUBSCRIPTION_TIER,
        tier=data.subscription_tier,
    )
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
    return _to_tenant_response(tenant)


@router.patch(
    "/{tenant_id}/azure-sso",
    response_model=TenantResponse,
    summary="Configure or disable Azure AD SSO for a tenant",
)
@transactional()
async def update_azure_sso(
    tenant_id: str,
    data: TenantAzureSsoRequest,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """
    Set or update Azure AD SSO config for a tenant.

    - Pass `azure_tenant_id` + `enabled=true` to wire SSO.
    - Pass `enabled=false` (with or without `azure_tenant_id`) to pause SSO without losing the stored ID.
    - Pass `azure_tenant_id=null` + `enabled=false` to fully clear.
    """
    tenant = await tenant_repo.get_by_id(TenantId(tenant_id))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if data.azure_tenant_id:
        tenant.configure_azure_sso(data.azure_tenant_id, enabled=data.enabled)
    else:
        # No new ID provided; just toggle the existing one (or no-op if never set).
        if data.enabled and not tenant.azure_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot enable Azure SSO without an azure_tenant_id",
            )
        tenant.azure_sso_enabled = data.enabled

    await tenant_repo.save(tenant)
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
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
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(TenantId(tenant_id), TenantTransition.ARCHIVE)
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
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
    use_case = TransitionUseCase(tenant_repo, "Tenant")
    tenant = await use_case.execute(TenantId(tenant_id), TenantTransition.RESTORE)
    await audit_change(tenant, audit_handler, current_user, request, tenant_id=tenant.id)
    return _to_tenant_response(tenant)


# ==================== QUERIES (Direct Repository) ====================


def _matches_filters(
    tenant: TenantEntity,
    status: TenantStatus | None,
    subscription_tier: SubscriptionTier | None,
    search: str | None,
) -> bool:
    """Apply the list filters to a single tenant.

    A non-platform user's list is their own tenant, so the filters have to be
    applied here rather than in the repository query.
    """
    if status is not None and tenant.status != status:
        return False
    if subscription_tier is not None and tenant.subscription_tier != subscription_tier:
        return False
    if search:
        needle = search.casefold()
        if needle not in tenant.name.casefold() and needle not in tenant.code.value.casefold():
            return False
    return True


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
    pg: PageParams = Depends(pagination()),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    current_user: TokenData = Depends(get_current_user),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    List tenants. Platform-admin users (members of PLATFORM_TENANT_ID) see all
    tenants; everyone else sees only their own tenant.
    """
    platform_tenant_id = (getattr(settings, "PLATFORM_TENANT_ID", "") or "").strip()
    is_platform_admin = bool(platform_tenant_id) and current_user.tenant_id == platform_tenant_id

    if not is_platform_admin:
        own = await tenant_repo.get_by_id(TenantId(current_user.tenant_id))
        items = [own] if own and _matches_filters(own, status, subscription_tier, search) else []
        return TenantListResponse(
            items=[_to_tenant_response(t) for t in items],
            total=len(items),
            page=1,
            limit=pg.limit,
            has_more=False,
        )

    tenants = await tenant_repo.list_all(
        status=status,
        subscription_tier=subscription_tier,
        search=search,
        limit=pg.limit,
        offset=pg.offset,
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
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
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
        raise NotFoundError("Tenant not found")
    user_count = await user_repo.count(tenant_id=TenantId(tenant_id))
    client_count = await client_repo.count(tenant_id=TenantId(tenant_id))

    # Calculate quota usage
    user_quota_usage = (
        (user_count / tenant.settings.max_users * 100) if tenant.settings.max_users > 0 else 0.0
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
        raise NotFoundError("Tenant not found")
    return _to_tenant_response(tenant)


@router.get(
    "/code/{code}",
    response_model=TenantResponse,
    summary="Get tenant by code",
)
@readonly()
async def get_tenant_by_code(
    code: str,
    current_user: TokenData = Depends(get_current_user),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tenant by code.

    Non-platform users can only resolve their own tenant by code (prevents
    cross-tenant enumeration via known codes).
    """
    tenant = await tenant_repo.get_by_code(code)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    platform_tenant_id = (getattr(settings, "PLATFORM_TENANT_ID", "") or "").strip()
    is_platform_admin = bool(platform_tenant_id) and current_user.tenant_id == platform_tenant_id
    if not is_platform_admin and tenant.id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only resolve your own tenant by code",
        )
    return _to_tenant_response(tenant)
