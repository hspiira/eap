"""
Security Module

Handles authentication, JWT tokens, and password hashing.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.domain.exceptions import AuthenticationException

# HTTP Bearer scheme for API docs and dependency injection (matches new_timeline style)
http_bearer = HTTPBearer(auto_error=False)


# =============================================================================
# TOKEN MODELS
# =============================================================================


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    user_id: str
    tenant_id: str
    email: str | None = None
    exp: datetime | None = None


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

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    """Create a refresh token with longer expiry."""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }
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
        return TokenData(user_id=user_id, tenant_id=tenant_id)
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

        return TokenData(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            exp=datetime.fromtimestamp(exp, tz=UTC) if exp else None,
        )
    except JWTError as e:
        raise AuthenticationException(f"Invalid token: {str(e)}")


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> TokenData | None:
    """
    Get current user from Bearer token if provided.

    This dependency does not require authentication - returns None
    if no token is provided.

    Args:
        credentials: Optional Bearer credentials from Authorization header

    Returns:
        TokenData if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return decode_token(credentials.credentials)
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
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Get current active user.

    Additional checks can be added here (e.g., check if user is banned).

    Args:
        current_user: Current authenticated user

    Returns:
        TokenData for active user
    """
    # Additional active user checks can be added here
    # For example, checking against database if user is still active
    return current_user


def require_tenant(tenant_id: str):
    """
    Create a dependency that requires a specific tenant.

    Args:
        tenant_id: Required tenant ID

    Returns:
        Dependency function that validates tenant
    """

    async def tenant_validator(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )
        return current_user

    return tenant_validator


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_token_response(
    user_id: str,
    tenant_id: str,
    email: str | None = None,
) -> Token:
    """Create access and refresh tokens."""
    access_token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        email=email,
    )
    refresh_token = create_refresh_token(user_id=user_id, tenant_id=tenant_id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
