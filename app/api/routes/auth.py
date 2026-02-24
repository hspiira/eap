"""
Authentication API Routes

FastAPI routes for authentication operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_tenant_repository, get_user_repository
from app.core.login_rate_limit import check_login_rate_limit, record_login_attempt
from app.api.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.application.use_cases.user_use_cases import RecordUserLoginUseCase
from app.core.database import get_db
from app.core.security import (
    create_token_response,
    decode_refresh_token,
    verify_password,
)
from app.domain.enums import TenantStatus, UserStatus
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.decorators import transactional

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and get access token",
)
@transactional()
async def login(
    request_body: LoginRequest,
    request: Request,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user with tenant code, email, and password.
    
    Returns a JWT access token that can be used for subsequent API requests.
    The token includes user_id, tenant_id, and email in its claims.
    
    Args:
        request_body: Login credentials (tenant_code, email, password)
        request: HTTP request (for rate limit and IP)
        tenant_repo: Tenant repository
        user_repo: User repository
        db: Database session
        
    Returns:
        LoginResponse with access token and user information
        
    Raises:
        HTTPException: If authentication fails (401) or rate limit exceeded (429)
    """
    check_login_rate_limit(request)
    record_login_attempt(request)

    # Get tenant by code
    tenant = await tenant_repo.get_by_code(request_body.tenant_code)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant code or credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if tenant is active
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant is {tenant.status.value.lower()}. Access denied.",
        )

    # Get user by email within tenant
    tenant_id = TenantId(tenant.id.value)
    email = Email(request_body.email)
    user = await user_repo.get_by_email(email, tenant_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant code or credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user has a password set
    # Access private field for authentication purposes
    password_hash = getattr(user, "_password_hash", None)
    if not password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password not set for this user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(request_body.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant code or credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active (not banned, terminated, or suspended)
    if user.status in (UserStatus.BANNED, UserStatus.TERMINATED, UserStatus.SUSPENDED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user.status.value.lower()}. Access denied.",
        )

    # Record login
    record_login_use_case = RecordUserLoginUseCase(user_repo)
    await record_login_use_case.execute(user.id)

    # Create and return token
    token = create_token_response(
        user_id=user.id.value,
        tenant_id=tenant.id.value,
        email=user.email.value,
    )

    return LoginResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
        user_id=user.id.value,
        tenant_id=tenant.id.value,
        email=user.email.value,
    )


@router.post("/refresh", response_model=RefreshResponse, summary="Refresh access token")
@transactional()
async def refresh_token(
    request: RefreshRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """Exchange refresh token for new access and refresh tokens."""
    try:
        token_data = decode_refresh_token(request.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user and tenant still exist and are active
    user = await user_repo.get_by_id(UserId(token_data.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status in (UserStatus.BANNED, UserStatus.TERMINATED, UserStatus.SUSPENDED):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tenant = await tenant_repo.get_by_id(TenantId(token_data.tenant_id))
    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token_response(
        user_id=token_data.user_id,
        tenant_id=token_data.tenant_id,
        email=token_data.email,
    )

    return RefreshResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
    )
