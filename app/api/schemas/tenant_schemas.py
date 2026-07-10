"""
Tenant API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import SubscriptionTier, TenantStatus


class TenantSettingsCreate(BaseModel):
    """Tenant settings for creation."""

    max_users: int = Field(default=10, ge=1, description="Maximum users allowed")
    max_clients: int = Field(default=5, ge=1, description="Maximum clients allowed")
    features_enabled: list[str] = Field(
        default_factory=list, description="Enabled feature names"
    )
    custom_branding: bool = Field(
        default=False, description="Whether custom branding is enabled"
    )


class TenantCreate(BaseModel):
    """Request schema for creating a tenant."""

    name: SanitizedStr = Field(..., min_length=1, max_length=255, description="Tenant name")
    code: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Tenant code (lowercase alphanumeric with hyphens)",
    )
    admin_email: str | None = Field(
        None,
        max_length=255,
        description="Email for the tenant admin user. Defaults to admin_{code}@evexia.test if not provided.",
    )
    subscription_tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE, description="Subscription tier"
    )
    settings: TenantSettingsCreate = Field(
        default_factory=TenantSettingsCreate, description="Tenant settings"
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate tenant code format."""
        import re

        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", v):
            raise ValueError(
                "Code must be lowercase alphanumeric with optional hyphens"
            )
        return v.lower()

    @field_validator("admin_email")
    @classmethod
    def validate_admin_email(cls, v: str | None) -> str | None:
        if v is None:
            return v
        import re
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address")
        return v.lower().strip()


class TenantSettingsResponse(BaseModel):
    """Tenant settings response."""

    max_users: int
    max_clients: int
    features_enabled: list[str]
    custom_branding: bool


class TenantResponse(BaseModel):
    """Response schema for tenant."""

    id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Tenant name")
    code: str = Field(..., description="Tenant code")
    status: TenantStatus = Field(..., description="Tenant status")
    subscription_tier: SubscriptionTier = Field(..., description="Subscription tier")
    settings: TenantSettingsResponse = Field(..., description="Tenant settings")
    is_active: bool = Field(..., description="Whether tenant is active")
    azure_tenant_id: str | None = Field(
        None, description="Azure AD directory ID for SSO (tid claim)"
    )
    azure_sso_enabled: bool = Field(
        default=False, description="Whether Azure SSO is enabled"
    )
    admin_email: str | None = Field(
        None, description="Admin user email (only returned on creation)"
    )
    admin_password: str | None = Field(
        None,
        description="Admin password (only when SET_PASSWORD_BASE_URL is not set; otherwise use set_password_url)",
    )
    set_password_url: str | None = Field(
        None,
        description="URL for user to set initial password (when SET_PASSWORD_BASE_URL is set)",
    )
    set_password_expires_at: datetime | None = Field(
        None,
        description="When the set-password link expires",
    )

    model_config = ConfigDict(from_attributes=True)


class TenantUpdateSettings(BaseModel):
    """Request schema for updating tenant settings."""

    max_users: int | None = Field(None, ge=1, description="Maximum users allowed")
    max_clients: int | None = Field(None, ge=1, description="Maximum clients allowed")
    features_enabled: list[str] | None = Field(
        None, description="Enabled feature names"
    )
    custom_branding: bool | None = Field(
        None, description="Whether custom branding is enabled"
    )


class TenantSuspendRequest(BaseModel):
    """Request schema for suspending a tenant."""

    reason: SanitizedStr = Field(..., min_length=1, description="Suspension reason")


class TenantTerminateRequest(BaseModel):
    """Request schema for terminating a tenant."""

    reason: SanitizedStr = Field(..., min_length=1, description="Termination reason")


class TenantUpdate(BaseModel):
    """Request schema for updating tenant basic information."""

    name: OptionalSanitizedStr = Field(None, min_length=1, max_length=255, description="Tenant name")


class TenantAzureSsoRequest(BaseModel):
    """Request schema for configuring or disabling Azure AD SSO on a tenant."""

    azure_tenant_id: str | None = Field(
        None,
        min_length=1,
        max_length=64,
        description="Azure AD directory ID (tid). Required when enabling SSO.",
    )
    enabled: bool = Field(
        default=True,
        description="Whether SSO is active. Set false to keep the ID but pause sign-in.",
    )


class SubscriptionUpdateRequest(BaseModel):
    """Request schema for updating subscription tier."""

    subscription_tier: SubscriptionTier = Field(..., description="New subscription tier")


class TenantStatsResponse(BaseModel):
    """Response schema for tenant statistics."""

    tenant_id: str = Field(..., description="Tenant identifier")
    current_user_count: int = Field(..., description="Current number of users")
    current_client_count: int = Field(..., description="Current number of clients")
    max_users: int = Field(..., description="Maximum users allowed")
    max_clients: int = Field(..., description="Maximum clients allowed")
    user_quota_usage: float = Field(..., description="User quota usage percentage")
    client_quota_usage: float = Field(..., description="Client quota usage percentage")
    subscription_tier: SubscriptionTier = Field(..., description="Subscription tier")


class TenantListResponse(BaseModel):
    """Response schema for tenant list."""

    items: list[TenantResponse] = Field(..., description="List of tenants")
    total: int = Field(..., description="Total number of tenants matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
