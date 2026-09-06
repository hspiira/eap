"""Provider API contracts independent of the legacy Person aggregate."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.api.schemas.provider_profile_schemas import ProviderProfileSchema
from app.domain.enums import BaseStatus


class ProviderResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    display_name: str | None
    email: str
    status: BaseStatus
    license_info: dict | None = None
    provider_profile: ProviderProfileSchema
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProviderCreate(BaseModel):
    user_id: str
    provider_profile: ProviderProfileSchema
    license_info: dict | None = None


class ProviderUpdate(BaseModel):
    provider_profile: ProviderProfileSchema | None = None
    license_info: dict | None = None
    status: BaseStatus | None = None


class ProviderListResponse(BaseModel):
    items: list[ProviderResponse]
    total: int
    has_more: bool
