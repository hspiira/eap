"""
Authentication API Schemas (DTOs)

Pydantic models for authentication request/response validation.
"""

import re
from pydantic import BaseModel, Field, field_validator

from app.core.security import Token


def validate_email_with_test(email: str) -> str:
    """
    Validate email address, allowing .test domains for admin users.
    
    This validator accepts standard email formats plus .test domains
    which are used for automatically created admin users.
    """
    # Standard email regex pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    # Check if it's a .test domain (used for admin users)
    test_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.test$"
    
    if re.match(test_pattern, email):
        return email
    
    # Otherwise validate as standard email
    if re.match(email_pattern, email):
        return email
    
    raise ValueError("Invalid email address format")


class LoginRequest(BaseModel):
    """Request schema for user login."""

    tenant_code: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Tenant code (3-15 characters, lowercase alphanumeric with optional hyphens)",
    )
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email address, allowing .test domains."""
        return validate_email_with_test(v)


class LoginResponse(BaseModel):
    """Response schema for successful login."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    email: str = Field(..., description="User email address")


class RefreshRequest(BaseModel):
    """Request schema for token refresh. refresh_token optional when using cookie auth."""

    refresh_token: str | None = Field(None, description="JWT refresh token")


class LogoutRequest(BaseModel):
    """Request schema for logout (revoke refresh token). refresh_token optional when using cookie auth."""

    refresh_token: str | None = Field(None, description="JWT refresh token to revoke")


class RefreshResponse(BaseModel):
    """Response schema for token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    """Response schema for GET /auth/me (current user from token or cookie)."""

    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    email: str = Field(..., description="User email address")
