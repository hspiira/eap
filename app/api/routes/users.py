"""
User API Routes

FastAPI routes for User operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import (
    get_user_in_tenant,
    require_same_tenant,
    require_tenant_role,
)
from app.core.security import TokenData, get_current_user
from app.domain.enums import TenantRole

from app.api.dependencies import get_audit_event_handler, get_tenant_repository, get_user_repository
from app.api.schemas.user_schemas import (
    UserBanRequest,
    UserCreate,
    UserDeactivateRequest,
    UserListResponse,
    UserResponse,
    UserSuspendRequest,
    UserTerminateRequest,
    UserUpdatePasswordRequest,
    UserUpdatePreferencesRequest,
)
from app.application.use_cases.transitions import (
    TransitionUseCase,
    UserTransition,
)
from app.application.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
)
from app.core.database import get_db
from app.domain.enums import UserStatus
from app.domain.entities.user import UserEntity
from app.domain.exceptions import EvexiaException
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/users", tags=["users"])


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    from app.core.security import hash_password
    return hash_password(password)


def _to_user_response(user: UserEntity) -> UserResponse:
    """Map UserEntity to API response using public properties."""
    return UserResponse(
        id=user.id.value,
        tenant_id=user.tenant_id.value,
        email=user.email.value,
        status=user.status,
        is_email_verified=user.is_email_verified,
        email_verified_at=user.email_verified_at,
        is_two_factor_enabled=user.is_two_factor_enabled,
        preferred_language=user.preferred_language,
        timezone=user.timezone,
        last_login_at=user.last_login_at,
        status_changed_at=user.status_changed_at,
        is_active=user.is_active(),
        role=user.role,
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
@transactional()
async def create_user(
    data: UserCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    password_hash = _hash_password(data.password) if data.password else None

    try:
        user = await CreateUserUseCase(user_repo, tenant_repo).execute(
            user_id=UserId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            email=Email(data.email),
            password_hash=password_hash,
        )
    except EvexiaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)

    if data.preferred_language or data.timezone:
        user_transition: TransitionUseCase = TransitionUseCase(user_repo)
        user_transition.entity_name = "User"
        user = await user_transition.execute(
            user.id,
            UserTransition.UPDATE_PREFERENCES,
            preferred_language=data.preferred_language,
            timezone=data.timezone,
        )

    await audit_entity_operation(
        entity=user,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(user)


@router.post(
    "/{user_id}/verify-email",
    response_model=UserResponse,
    summary="Verify user email",
)
@transactional()
async def verify_user_email(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Verify user email address."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.VERIFY_EMAIL)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate a user",
)
@transactional()
async def activate_user(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a user."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.ACTIVATE)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/suspend",
    response_model=UserResponse,
    summary="Suspend a user",
)
@transactional()
async def suspend_user(
    request: Request,
    body: UserSuspendRequest,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a user."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.SUSPEND, reason=body.reason)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/ban",
    response_model=UserResponse,
    summary="Ban a user",
)
@transactional()
async def ban_user(
    request: Request,
    body: UserBanRequest,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Ban a user."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.BAN, reason=body.reason)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate a user",
)
@transactional()
async def deactivate_user(
    request: Request,
    body: UserDeactivateRequest,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.DEACTIVATE, reason=body.reason)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/terminate",
    response_model=UserResponse,
    summary="Terminate a user",
)
@transactional()
async def terminate_user(
    request: Request,
    body: UserTerminateRequest,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a user."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.TERMINATE, reason=body.reason)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.patch(
    "/{user_id}/password",
    response_model=UserResponse,
    summary="Update user password",
)
@transactional()
async def update_user_password(
    request: Request,
    body: UserUpdatePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update user password."""
    password_hash = _hash_password(body.password)
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(
        user.id, UserTransition.UPDATE_PASSWORD, password_hash=password_hash
    )
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.patch(
    "/{user_id}/preferences",
    response_model=UserResponse,
    summary="Update user preferences",
)
@transactional()
async def update_user_preferences(
    request: Request,
    body: UserUpdatePreferencesRequest,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(
        user.id,
        UserTransition.UPDATE_PREFERENCES,
        preferred_language=body.preferred_language,
        timezone=body.timezone,
    )
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/enable-2fa",
    response_model=UserResponse,
    summary="Enable two-factor authentication",
)
@transactional()
async def enable_two_factor(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Enable two-factor authentication for a user."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.ENABLE_TWO_FACTOR)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/disable-2fa",
    response_model=UserResponse,
    summary="Disable two-factor authentication",
)
@transactional()
async def disable_two_factor(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Disable two-factor authentication for a user."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.DISABLE_TWO_FACTOR)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


@router.post(
    "/{user_id}/record-login",
    response_model=UserResponse,
    summary="Record user login",
)
@transactional()
async def record_user_login(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    user: UserEntity = Depends(get_user_in_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Record user login (updates last_login_at)."""
    use_case: TransitionUseCase = TransitionUseCase(user_repo)
    use_case.entity_name = "User"
    updated_user = await use_case.execute(user.id, UserTransition.RECORD_LOGIN)
    await audit_entity_operation(
        entity=updated_user,
        audit_handler=audit_handler,
        tenant_id=updated_user.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_user_response(updated_user)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users with filtering and pagination",
)
@readonly()
async def list_users(
    tenant_id: str = Query(..., description="Tenant identifier"),
    status: UserStatus | None = Query(None, description="Filter by user status"),
    is_email_verified: bool | None = Query(None, description="Filter by email verification status"),
    search: str | None = Query(None, description="Search in user email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    current_user: TokenData = Depends(require_same_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """List users with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    users = await user_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        is_email_verified=is_email_verified,
        search=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await user_repo.count(
        tenant_id=TenantId(tenant_id),
        status=status,
        is_email_verified=is_email_verified,
        search=search,
    )

    return UserListResponse(
        items=[_to_user_response(user) for user in users],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
@readonly()
async def get_user(
    user: UserEntity = Depends(get_user_in_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID."""
    return _to_user_response(user)


@router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Get user by email",
)
@readonly()
async def get_user_by_email(
    email: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get user by email within a tenant."""
    user = await GetUserUseCase(user_repo).execute_by_email(Email(email), TenantId(tenant_id))
    if not user:
        raise ValueError("User not found")
    return _to_user_response(user)


@router.get(
    "/check-email/{email}",
    summary="Check if user email is available",
)
@readonly()
async def check_email_availability(
    email: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a user email is available within a tenant."""
    user = await GetUserUseCase(user_repo).execute_by_email(Email(email), TenantId(tenant_id))
    return {"available": user is None, "email": email, "tenant_id": tenant_id}
