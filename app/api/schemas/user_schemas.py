"""
User API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.domain.enums import Language, TenantRole, UserStatus


# === Request Schemas ===

class UserCreate(BaseModel):
    """Request schema for creating a user."""

    email: EmailStr = Field(..., description="User email address")
    password: str | None = Field(None, min_length=8, description="User password (will be hashed)")
    preferred_language: Language | None = Field(None, description="Preferred language")
    timezone: str | None = Field(None, description="User timezone")


class UserSuspendRequest(BaseModel):
    """Request schema for suspending a user."""

    reason: str = Field(..., min_length=1, description="Suspension reason")


class UserBanRequest(BaseModel):
    """Request schema for banning a user."""

    reason: str = Field(..., min_length=1, description="Ban reason")


class UserDeactivateRequest(BaseModel):
    """Request schema for deactivating a user."""

    reason: str | None = Field(None, description="Deactivation reason")


class UserTerminateRequest(BaseModel):
    """Request schema for terminating a user."""

    reason: str = Field(..., min_length=1, description="Termination reason")


class UserUpdatePasswordRequest(BaseModel):
    """Request schema for updating user password."""

    password: str = Field(..., min_length=8, description="New password (will be hashed)")


class UserUpdatePreferencesRequest(BaseModel):
    """Request schema for updating user preferences."""

    preferred_language: Language | None = Field(None, description="Preferred language")
    timezone: str | None = Field(None, description="User timezone")

    @model_validator(mode="after")
    def _validate_preferences(self) -> 'UserUpdatePreferencesRequest':
        if self.preferred_language is None and self.timezone is None:
            raise ValueError("At least one preference (preferred_language or timezone) must be provided")
        return self


# === Response Schemas ===

class UserResponse(BaseModel):
    """Response schema for user."""

    id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    email: str = Field(..., description="User email address")
    status: UserStatus = Field(..., description="User status")
    is_email_verified: bool = Field(..., description="Whether email is verified")
    email_verified_at: datetime | None = Field(None, description="Email verification timestamp")
    is_two_factor_enabled: bool = Field(..., description="Whether 2FA is enabled")
    preferred_language: Language | None = Field(None, description="Preferred language")
    timezone: str | None = Field(None, description="User timezone")
    last_login_at: datetime | None = Field(None, description="Last login timestamp")
    status_changed_at: datetime | None = Field(None, description="Status change timestamp")
    is_active: bool = Field(..., description="Whether user is active")
    role: TenantRole = Field(..., description="Tenant role (Admin, User, Viewer)")

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Response schema for user list."""

    items: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
