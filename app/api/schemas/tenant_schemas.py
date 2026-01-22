"""
Tenant API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from pydantic import BaseModel, Field, field_validator

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

    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    code: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Tenant code (lowercase alphanumeric with hyphens)",
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

    class Config:
        from_attributes = True


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

    reason: str = Field(..., min_length=1, description="Suspension reason")


class TenantTerminateRequest(BaseModel):
    """Request schema for terminating a tenant."""

    reason: str = Field(..., min_length=1, description="Termination reason")
