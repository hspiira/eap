"""
User API Routes

FastAPI routes for User operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_user_repository
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
from app.application.use_cases.user_use_cases import (
    ActivateUserUseCase,
    BanUserUseCase,
    CreateUserUseCase,
    DeactivateUserUseCase,
    DisableTwoFactorUseCase,
    EnableTwoFactorUseCase,
    GetUserUseCase,
    RecordUserLoginUseCase,
    SuspendUserUseCase,
    TerminateUserUseCase,
    UpdateUserPasswordUseCase,
    UpdateUserPreferencesUseCase,
    VerifyUserEmailUseCase,
)
from app.core.database import get_db
from app.domain.enums import UserStatus
from app.domain.entities.user import UserEntity
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid

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
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    password_hash = _hash_password(data.password) if data.password else None

    user = await CreateUserUseCase(user_repo).execute(
        user_id=UserId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        email=Email(data.email),
        password_hash=password_hash,
    )

    if data.preferred_language or data.timezone:
        user = await UpdateUserPreferencesUseCase(user_repo).execute(
            user.id,
            preferred_language=data.preferred_language,
            timezone=data.timezone,
        )

    return _to_user_response(user)


@router.post(
    "/{user_id}/verify-email",
    response_model=UserResponse,
    summary="Verify user email",
)
@transactional()
async def verify_user_email(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Verify user email address."""
    user = await VerifyUserEmailUseCase(user_repo).execute(UserId(user_id))
    return _to_user_response(user)


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate a user",
)
@transactional()
async def activate_user(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Activate a user."""
    user = await ActivateUserUseCase(user_repo).execute(UserId(user_id))
    return _to_user_response(user)


@router.post(
    "/{user_id}/suspend",
    response_model=UserResponse,
    summary="Suspend a user",
)
@transactional()
async def suspend_user(
    user_id: str,
    request: UserSuspendRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a user."""
    user = await SuspendUserUseCase(user_repo).execute(UserId(user_id), request.reason)
    return _to_user_response(user)


@router.post(
    "/{user_id}/ban",
    response_model=UserResponse,
    summary="Ban a user",
)
@transactional()
async def ban_user(
    user_id: str,
    request: UserBanRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Ban a user."""
    user = await BanUserUseCase(user_repo).execute(UserId(user_id), request.reason)
    return _to_user_response(user)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate a user",
)
@transactional()
async def deactivate_user(
    user_id: str,
    request: UserDeactivateRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user."""
    user = await DeactivateUserUseCase(user_repo).execute(UserId(user_id), request.reason)
    return _to_user_response(user)


@router.post(
    "/{user_id}/terminate",
    response_model=UserResponse,
    summary="Terminate a user",
)
@transactional()
async def terminate_user(
    user_id: str,
    request: UserTerminateRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a user."""
    user = await TerminateUserUseCase(user_repo).execute(UserId(user_id), request.reason)
    return _to_user_response(user)


@router.patch(
    "/{user_id}/password",
    response_model=UserResponse,
    summary="Update user password",
)
@transactional()
async def update_user_password(
    user_id: str,
    request: UserUpdatePasswordRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update user password."""
    password_hash = _hash_password(request.password)
    user = await UpdateUserPasswordUseCase(user_repo).execute(UserId(user_id), password_hash)
    return _to_user_response(user)


@router.patch(
    "/{user_id}/preferences",
    response_model=UserResponse,
    summary="Update user preferences",
)
@transactional()
async def update_user_preferences(
    user_id: str,
    request: UserUpdatePreferencesRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences."""
    user = await UpdateUserPreferencesUseCase(user_repo).execute(
        UserId(user_id),
        preferred_language=request.preferred_language,
        timezone=request.timezone,
    )
    return _to_user_response(user)


@router.post(
    "/{user_id}/enable-2fa",
    response_model=UserResponse,
    summary="Enable two-factor authentication",
)
@transactional()
async def enable_two_factor(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Enable two-factor authentication for a user."""
    user = await EnableTwoFactorUseCase(user_repo).execute(UserId(user_id))
    return _to_user_response(user)


@router.post(
    "/{user_id}/disable-2fa",
    response_model=UserResponse,
    summary="Disable two-factor authentication",
)
@transactional()
async def disable_two_factor(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Disable two-factor authentication for a user."""
    user = await DisableTwoFactorUseCase(user_repo).execute(UserId(user_id))
    return _to_user_response(user)


@router.post(
    "/{user_id}/record-login",
    response_model=UserResponse,
    summary="Record user login",
)
@transactional()
async def record_user_login(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Record user login (updates last_login_at)."""
    user = await RecordUserLoginUseCase(user_repo).execute(UserId(user_id))
    return _to_user_response(user)


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
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID."""
    user = await user_repo.get_by_id(UserId(user_id))
    if not user:
        raise ValueError("User not found")
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
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a user email is available within a tenant."""
    user = await GetUserUseCase(user_repo).execute_by_email(Email(email), TenantId(tenant_id))
    return {"available": user is None, "email": email, "tenant_id": tenant_id}
