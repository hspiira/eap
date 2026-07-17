"""
Base API Schemas

Generic base classes for API request/response schemas.
Free-text fields use SanitizedStr so stored values are sanitized at the API boundary.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from app.shared.utils.sanitization import InputSanitizer


def _sanitize_html(v: str | None) -> str | None:
    """Sanitize string for storage; leave None unchanged."""
    if v is None:
        return None
    if isinstance(v, str):
        return InputSanitizer.sanitize_html(v)
    return v


# Use for free-text request fields (name, description, reason, notes, address, etc.)
SanitizedStr = Annotated[str, BeforeValidator(_sanitize_html)]
OptionalSanitizedStr = Annotated[str | None, BeforeValidator(_sanitize_html)]


class BaseEntityResponse(BaseModel):
    """
    Base response schema for entity responses.

    Provides common fields that all entities have.
    """

    id: str = Field(..., description="Unique identifier")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class TenantScopedResponse(BaseEntityResponse):
    """
    Base response for tenant-scoped entities.
    """

    tenant_id: str = Field(..., description="Tenant identifier")


class StatusResponse(BaseModel):
    """Generic status response for lifecycle operations."""

    id: str = Field(..., description="Entity identifier")
    status: str = Field(..., description="Current status")
    updated_at: datetime = Field(..., description="When status was updated")


class ActionRequest(BaseModel):
    """Base request for actions requiring a reason."""

    reason: SanitizedStr = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Reason for the action",
    )


class OptionalReasonRequest(BaseModel):
    """Request where reason is optional."""

    reason: OptionalSanitizedStr = Field(
        None,
        max_length=500,
        description="Optional reason for the action",
    )
