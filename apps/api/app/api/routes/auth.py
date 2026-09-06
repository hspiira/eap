"""
Authentication API Routes

FastAPI routes for authentication operations.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_password_set_token_repository,
    get_refresh_token_repository,
    get_tenant_repository,
    get_user_repository,
)
from app.api.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    SetInitialPasswordRequest,
)
from app.core.authorization import is_platform_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.login_rate_limit import check_login_rate_limit, record_login_attempt
from app.core.security import (
    COOKIE_ACCESS_TOKEN,
    COOKIE_REFRESH_TOKEN,
    TokenData,
    create_token_response,
    decode_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.domain.enums import TenantStatus, UserStatus
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.infrastructure.repositories.password_set_token_repository import (
    PasswordSetTokenRepository,
)
from app.infrastructure.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.shared.decorators import transactional
from app.shared.utils.generators import generate_cuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/set-initial-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Set initial admin password using one-time token",
)
@transactional()
async def set_initial_password(
    body: SetInitialPasswordRequest,
    password_set_token_repo: PasswordSetTokenRepository = Depends(
        get_password_set_token_repository
    ),
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Set the initial admin password using the one-time token from the
    set_password_url returned when creating a tenant (when SET_PASSWORD_BASE_URL is set).
    After calling this, the user can log in with tenant code, admin email, and this password.
    """
    user_id = await password_set_token_repo.redeem(body.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired link. Request a new link from your administrator.",
        )
    password_hash = hash_password(body.password)
    updated = await user_repo.update_password(UserId(user_id), password_hash)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )
    return None


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user from token or cookie",
)
async def auth_me(
    current_user: TokenData = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Return current user identity (user_id, tenant_id, email, role).

    Falls back to the DB for email and role since legacy JWTs may not carry
    them; the BE is the source of truth.
    """
    email = current_user.email or ""
    role: str | None = None
    access_scopes: list[str] = list(current_user.access_scopes)
    try:
        user = await user_repo.get_by_id(UserId(current_user.user_id))
        if user:
            email = user.email.value
            role = user.role.value
            access_scopes = [sc.value for sc in user.access_scopes]
    except Exception:
        # Degrade to token-only identity rather than failing /me, but do not let a
        # DB outage look like a healthy response with a missing role.
        logger.warning(
            "auth.me: user lookup failed; falling back to token claims",
            extra={"user_id": current_user.user_id},
            exc_info=True,
        )
    return MeResponse(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        email=email,
        role=role,
        access_scopes=access_scopes,
        is_platform_admin=is_platform_admin(current_user),
    )


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
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
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

    tenant_id = TenantId(tenant.id.value)
    email = Email(request_body.email)
    user = await user_repo.get_by_email(email, tenant_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant code or credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to repeated failed sign-in attempts. Try again later.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_hash = getattr(user, "_password_hash", None)
    lockout_threshold = settings.LOGIN_LOCKOUT_THRESHOLD
    lockout_window = timedelta(minutes=settings.LOGIN_LOCKOUT_DURATION_MINUTES)

    if not password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password not set for this user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(request_body.password, password_hash):
        user.record_failed_login(
            threshold=lockout_threshold,
            lock_duration=lockout_window,
        )
        await user_repo.save(user)
        # Commit before raising. @transactional rolls back on HTTPException, and
        # a failed login always ends in one, so without this the counter is
        # discarded every time and the account lockout never fires.
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant code or credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status in (UserStatus.BANNED, UserStatus.TERMINATED, UserStatus.SUSPENDED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user.status.value.lower()}. Access denied.",
        )

    user.record_successful_login()
    await user_repo.save(user)

    # Optionally revoke all previous refresh tokens for this user before issuing a new one
    if getattr(settings, "REVOKE_PREVIOUS_REFRESH_TOKENS_ON_LOGIN", False) and refresh_token_repo:
        await refresh_token_repo.revoke_all_for_user(user.id.value)

    # Create and return token (store refresh jti when revocation is enabled)
    refresh_jti = None
    if getattr(settings, "REFRESH_TOKEN_REVOCATION", False) and refresh_token_repo:
        refresh_jti = generate_cuid()
    token = create_token_response(
        user_id=user.id.value,
        tenant_id=tenant.id.value,
        email=user.email.value,
        refresh_jti=refresh_jti,
        role=user.role.value if user.role else None,
        access_scopes=[sc.value for sc in user.access_scopes],
    )
    if refresh_jti:
        await refresh_token_repo.save(refresh_jti, user.id.value, tenant.id.value)

    login_response = LoginResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
        user_id=user.id.value,
        tenant_id=tenant.id.value,
        email=user.email.value,
    )

    if getattr(settings, "AUTH_USE_HTTPONLY_COOKIES", False):
        secure = not settings.is_development
        access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        response = JSONResponse(content=login_response.model_dump())
        response.set_cookie(
            key=COOKIE_ACCESS_TOKEN,
            value=token.access_token,
            max_age=access_max_age,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key=COOKIE_REFRESH_TOKEN,
            value=token.refresh_token,
            max_age=refresh_max_age,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )
        return response

    return login_response


@router.post("/refresh", response_model=RefreshResponse, summary="Refresh access token")
@transactional()
async def refresh_token(
    request: Request,
    body: RefreshRequest | None = Body(None),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    db: AsyncSession = Depends(get_db),
):
    """Exchange refresh token for new access and refresh tokens. Optionally rotates refresh token."""
    refresh_token_value = None
    if getattr(settings, "AUTH_USE_HTTPONLY_COOKIES", False):
        refresh_token_value = request.cookies.get(COOKIE_REFRESH_TOKEN)
    if not refresh_token_value and body is not None:
        refresh_token_value = body.refresh_token
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token_data = decode_refresh_token(refresh_token_value)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    # When revocation is enabled, require stored token and ensure it is not revoked
    if getattr(settings, "REFRESH_TOKEN_REVOCATION", False) and token_data.jti:
        valid = await refresh_token_repo.is_valid(token_data.jti)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
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

    # Rotation: issue new refresh token and revoke old one; otherwise reuse same jti
    rotation = getattr(settings, "REFRESH_TOKEN_ROTATION", True)
    refresh_jti = token_data.jti  # reuse for same token when not rotating
    if rotation:
        refresh_jti = generate_cuid()
        if token_data.jti:
            await refresh_token_repo.revoke(token_data.jti)
    token = create_token_response(
        user_id=token_data.user_id,
        tenant_id=token_data.tenant_id,
        email=token_data.email,
        refresh_jti=refresh_jti,
        role=user.role.value if user.role else None,
        access_scopes=[sc.value for sc in user.access_scopes],
    )
    if rotation:
        await refresh_token_repo.save(refresh_jti, token_data.user_id, token_data.tenant_id)

    refresh_response = RefreshResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
    )

    if getattr(settings, "AUTH_USE_HTTPONLY_COOKIES", False):
        secure = not settings.is_development
        access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        response = JSONResponse(content=refresh_response.model_dump())
        response.set_cookie(
            key=COOKIE_ACCESS_TOKEN,
            value=token.access_token,
            max_age=access_max_age,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key=COOKIE_REFRESH_TOKEN,
            value=token.refresh_token,
            max_age=refresh_max_age,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )
        return response

    return refresh_response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token (logout)",
)
@transactional()
async def logout(
    request: Request,
    body: LogoutRequest | None = Body(None),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a refresh token so it can no longer be used. No-op if token has no jti or revocation is disabled."""
    refresh_token_value = None
    if getattr(settings, "AUTH_USE_HTTPONLY_COOKIES", False):
        refresh_token_value = request.cookies.get(COOKIE_REFRESH_TOKEN)
    if not refresh_token_value and body is not None:
        refresh_token_value = body.refresh_token
    if getattr(settings, "REFRESH_TOKEN_REVOCATION", False) and refresh_token_value:
        jti: str | None = None
        try:
            token_data = decode_refresh_token(refresh_token_value)
            jti = token_data.jti
            if jti:
                await refresh_token_repo.revoke(jti)
        except Exception:
            # Logout still succeeds (cookies are cleared below), but an unrevoked
            # refresh token remains usable until it expires; that needs a trail.
            logger.warning(
                "auth.logout: refresh token revocation failed; token may remain valid until expiry",
                extra={"jti": jti},
                exc_info=True,
            )
    if getattr(settings, "AUTH_USE_HTTPONLY_COOKIES", False):
        from fastapi.responses import Response

        secure = not settings.is_development
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            key=COOKIE_ACCESS_TOKEN,
            path="/",
            secure=secure,
            samesite="lax",
            httponly=True,
        )
        response.delete_cookie(
            key=COOKIE_REFRESH_TOKEN,
            path="/",
            secure=secure,
            samesite="lax",
            httponly=True,
        )
        return response
    return None


# =============================================================================
# AZURE AD SSO: Option C (Sign in with Microsoft, no tenant code required)
# =============================================================================
