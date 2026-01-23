"""
Authentication API Routes

FastAPI routes for authentication operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_tenant_repository, get_user_repository
from app.api.schemas.auth_schemas import LoginRequest, LoginResponse
from app.application.use_cases.user_use_cases import RecordUserLoginUseCase
from app.core.database import get_db
from app.core.security import create_token_response, verify_password
from app.domain.enums import TenantStatus, UserStatus
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId
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
    request: LoginRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user with tenant code, email, and password.
    
    Returns a JWT access token that can be used for subsequent API requests.
    The token includes user_id, tenant_id, and email in its claims.
    
    Args:
        request: Login credentials (tenant_code, email, password)
        tenant_repo: Tenant repository
        user_repo: User repository
        db: Database session
        
    Returns:
        LoginResponse with access token and user information
        
    Raises:
        HTTPException: If authentication fails (401)
    """
    # Get tenant by code
    tenant = await tenant_repo.get_by_code(request.tenant_code)
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
    email = Email(request.email)
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
    if not verify_password(request.password, password_hash):
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
        token_type=token.token_type,
        expires_in=token.expires_in,
        user_id=user.id.value,
        tenant_id=tenant.id.value,
        email=user.email.value,
    )
