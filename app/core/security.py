"""
Security Module

Handles authentication, JWT tokens, and password hashing.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.domain.exceptions import AuthenticationException

# HTTP Bearer scheme for API docs and dependency injection (matches new_timeline style)
http_bearer = HTTPBearer(auto_error=False)

# Cookie names when AUTH_USE_HTTPONLY_COOKIES is enabled
COOKIE_ACCESS_TOKEN = "evexia_access_token"
COOKIE_REFRESH_TOKEN = "evexia_refresh_token"


# =============================================================================
# TOKEN MODELS
# =============================================================================


class TokenData(BaseModel):
    """Data extracted from JWT token.

    ``access_scopes`` carries the bounded-context split that gates the privacy
    wall (see ``AccessScope`` / 5A.2). Tokens minted before the scope rollout
    have an empty list; the route guards treat that as legacy
    PLATFORM_ADMIN — clinical-only routes will still refuse them once the
    auth backend starts emitting explicit scopes.
    """

    user_id: str
    tenant_id: str
    email: str | None = None
    exp: datetime | None = None
    jti: str | None = None
    access_scopes: list[str] = []


class Token(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# =============================================================================
# PASSWORD HASHING
# =============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# =============================================================================
# JWT TOKEN FUNCTIONS
# =============================================================================


def create_access_token(
    user_id: str,
    tenant_id: str,
    email: str | None = None,
    additional_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
    access_scopes: list[str] | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        email: User email (optional)
        additional_claims: Extra claims to include in the token
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode: dict[str, Any] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    if email:
        to_encode["email"] = email

    if access_scopes:
        to_encode["access_scopes"] = list(access_scopes)

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    user_id: str,
    tenant_id: str,
    jti: str | None = None,
) -> str:
    """Create a refresh token with longer expiry. Optional jti for revocation."""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }
    if jti:
        to_encode["jti"] = jti
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_refresh_token(token: str) -> TokenData:
    """Decode refresh token and validate it's a refresh token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise AuthenticationException("Invalid token type")
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not user_id or not tenant_id:
            raise AuthenticationException("Invalid token: missing claims")
        jti = payload.get("jti")
        return TokenData(
            user_id=user_id,
            tenant_id=tenant_id,
            jti=jti,
        )
    except JWTError as e:
        raise AuthenticationException(f"Invalid refresh token: {str(e)}")


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData with extracted claims

    Raises:
        AuthenticationException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        email: str | None = payload.get("email")
        exp: datetime | None = payload.get("exp")

        if user_id is None or tenant_id is None:
            raise AuthenticationException("Invalid token: missing required claims")

        scopes_claim = payload.get("access_scopes") or []
        if not isinstance(scopes_claim, list):
            scopes_claim = []
        return TokenData(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            exp=datetime.fromtimestamp(exp, tz=UTC) if exp else None,
            access_scopes=[str(s) for s in scopes_claim],
        )
    except JWTError as e:
        raise AuthenticationException(f"Invalid token: {str(e)}")


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================


async def get_access_token_str(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> str | None:
    """
    Get access token from cookie (if AUTH_USE_HTTPONLY_COOKIES) or Bearer header.
    """
    if getattr(settings, "AUTH_USE_HTTPONLY_COOKIES", False):
        token = request.cookies.get(COOKIE_ACCESS_TOKEN)
        if token:
            return token
    if credentials:
        return credentials.credentials
    return None


async def get_current_user_optional(
    token_str: str | None = Depends(get_access_token_str),
) -> TokenData | None:
    """
    Get current user from Bearer token or cookie if provided.

    This dependency does not require authentication - returns None
    if no token is provided.

    Returns:
        TokenData if authenticated, None otherwise
    """
    if not token_str:
        return None

    try:
        return decode_token(token_str)
    except AuthenticationException:
        return None


async def get_current_user(
    current_user: TokenData | None = Depends(get_current_user_optional),
) -> TokenData:
    """
    Get current authenticated user.

    This dependency requires authentication - raises HTTPException
    if not authenticated.

    Args:
        current_user: Result of get_current_user_optional (None if not authenticated)

    Returns:
        TokenData for authenticated user

    Raises:
        HTTPException: If not authenticated
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_current_active_user(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Get current active user (same as get_current_user unless STRICT_ACTIVE_USER_CHECK is True).

    When STRICT_ACTIVE_USER_CHECK is True, re-validates user and tenant in DB and rejects if
    user is not active or tenant is not active. Otherwise returns token data without DB check.
    """
    validate = getattr(request.app.state, "validate_active_user", None)
    if validate is not None:
        await validate(request, current_user)
    return current_user


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_token_response(
    user_id: str,
    tenant_id: str,
    email: str | None = None,
    refresh_jti: str | None = None,
) -> Token:
    """Create access and refresh tokens. Optional refresh_jti for revocation support."""
    access_token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        email=email,
    )
    refresh_token = create_refresh_token(
        user_id=user_id,
        tenant_id=tenant_id,
        jti=refresh_jti,
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
