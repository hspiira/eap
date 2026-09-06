"""Global specialty vocabulary and tenant-owned practitioner links (decision 5)."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderSpecialtyId,
    ProviderSpecialtyLinkId,
)


@dataclass
class ProviderSpecialtyEntity:
    """A catalogue entry shared across tenants. Deliberately carries no tenant_id.

    Writes are platform-level. Retiring an entry stops new selection and keeps
    existing links readable.
    """

    id: ProviderSpecialtyId
    code: str
    label: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise DomainError("Specialty requires a code")
        if not self.label or not self.label.strip():
            raise DomainError("Specialty requires a label")

    def retire(self) -> None:
        self.is_active = False

    def restore(self) -> None:
        self.is_active = True


@dataclass
class ProviderSpecialtyLinkEntity:
    """A tenant's assertion that one of its practitioners holds a specialty.

    The link is tenant-owned even though the specialty it points at is global.
    """

    id: ProviderSpecialtyLinkId
    tenant_id: TenantId
    provider_id: ProviderId
    specialty_id: ProviderSpecialtyId
    created_at: datetime
