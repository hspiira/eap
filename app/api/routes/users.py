"""
User API Routes

FastAPI routes for User operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
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
from app.domain.enums import Language, UserStatus
from app.domain.entities.user import UserEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/users", tags=["users"])


def _hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hashed password string
    """
    from app.core.security import hash_password
    return hash_password(password)


def _to_user_response(user: UserEntity) -> UserResponse:
    """Map UserEntity to API response."""
    return UserResponse(
        id=user._id.value,
        tenant_id=user._tenant_id.value,
        email=user._email.value,
        status=user._status,
        is_email_verified=user._email_verified_at is not None,
        email_verified_at=user._email_verified_at,
        is_two_factor_enabled=user._is_two_factor_enabled,
        preferred_language=user._preferred_language,
        timezone=user._timezone,
        last_login_at=user._last_login_at,
        status_changed_at=user._status_changed_at,
        is_active=user.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    data: UserCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        # Hash password if provided
        password_hash = None
        if data.password:
            password_hash = _hash_password(data.password)

        create_use_case = CreateUserUseCase(user_repo)

        user = await create_use_case.execute(
            user_id=UserId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            email=Email(data.email),
            password_hash=password_hash,
        )

        # Set preferences if provided
        if data.preferred_language or data.timezone:
            update_prefs_use_case = UpdateUserPreferencesUseCase(user_repo)
            user = await update_prefs_use_case.execute(
                user._id,
                preferred_language=data.preferred_language,
                timezone=data.timezone,
            )

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/verify-email",
    response_model=UserResponse,
    summary="Verify user email",
)
async def verify_user_email(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify user email address.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        verify_use_case = VerifyUserEmailUseCase(user_repo)

        user = await verify_use_case.execute(UserId(user_id))

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate a user",
)
async def activate_user(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateUserUseCase(user_repo)

        user = await activate_use_case.execute(UserId(user_id))

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/suspend",
    response_model=UserResponse,
    summary="Suspend a user",
)
async def suspend_user(
    user_id: str,
    request: UserSuspendRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Suspend a user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        suspend_use_case = SuspendUserUseCase(user_repo)

        user = await suspend_use_case.execute(UserId(user_id), request.reason)

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/ban",
    response_model=UserResponse,
    summary="Ban a user",
)
async def ban_user(
    user_id: str,
    request: UserBanRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Ban a user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        ban_use_case = BanUserUseCase(user_repo)

        user = await ban_use_case.execute(UserId(user_id), request.reason)

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate a user",
)
async def deactivate_user(
    user_id: str,
    request: UserDeactivateRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        deactivate_use_case = DeactivateUserUseCase(user_repo)

        user = await deactivate_use_case.execute(UserId(user_id), request.reason)

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/terminate",
    response_model=UserResponse,
    summary="Terminate a user",
)
async def terminate_user(
    user_id: str,
    request: UserTerminateRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Terminate a user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        terminate_use_case = TerminateUserUseCase(user_repo)

        user = await terminate_use_case.execute(UserId(user_id), request.reason)

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{user_id}/password",
    response_model=UserResponse,
    summary="Update user password",
)
async def update_user_password(
    user_id: str,
    request: UserUpdatePasswordRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user password.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        password_hash = _hash_password(request.password)

        update_use_case = UpdateUserPasswordUseCase(user_repo)

        user = await update_use_case.execute(UserId(user_id), password_hash)

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{user_id}/preferences",
    response_model=UserResponse,
    summary="Update user preferences",
)
async def update_user_preferences(
    user_id: str,
    request: UserUpdatePreferencesRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user preferences.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateUserPreferencesUseCase(user_repo)

        user = await update_use_case.execute(
            UserId(user_id),
            preferred_language=request.preferred_language,
            timezone=request.timezone,
        )

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/enable-2fa",
    response_model=UserResponse,
    summary="Enable two-factor authentication",
)
async def enable_two_factor(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Enable two-factor authentication for a user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        enable_use_case = EnableTwoFactorUseCase(user_repo)

        user = await enable_use_case.execute(UserId(user_id))

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/disable-2fa",
    response_model=UserResponse,
    summary="Disable two-factor authentication",
)
async def disable_two_factor(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable two-factor authentication for a user.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        disable_use_case = DisableTwoFactorUseCase(user_repo)

        user = await disable_use_case.execute(UserId(user_id))

        await db.commit()

        return _to_user_response(user)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{user_id}/record-login",
    response_model=UserResponse,
    summary="Record user login",
)
async def record_user_login(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Record user login (updates last_login_at).

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        record_login_use_case = RecordUserLoginUseCase(user_repo)

        user = await record_login_use_case.execute(UserId(user_id))

        await db.commit()

        return _to_user_response(user)
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
    response_model=UserListResponse,
    summary="List users with filtering and pagination",
)
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
):
    """
    List users with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
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

    user_responses = [_to_user_response(user) for user in users]

    return UserListResponse(
        items=user_responses,
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
async def get_user(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Get user by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    user = await user_repo.get_by_id(UserId(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return _to_user_response(user)


@router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Get user by email",
)
async def get_user_by_email(
    email: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Get user by email within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetUserUseCase(user_repo)

    user = await get_use_case.execute_by_email(Email(email), TenantId(tenant_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return _to_user_response(user)


@router.get(
    "/check-email/{email}",
    summary="Check if user email is available",
)
async def check_email_availability(
    email: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Check if a user email is available within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetUserUseCase(user_repo)

    user = await get_use_case.execute_by_email(Email(email), TenantId(tenant_id))

    return {"available": user is None, "email": email, "tenant_id": tenant_id}
