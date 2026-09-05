"""Client alias domain entity."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects.core import ClientAliasId, ClientId, TenantId


@dataclass
class ClientAliasEntity:
    """A tenant-scoped alternate name belonging to one client."""

    id: ClientAliasId
    tenant_id: TenantId
    client_id: ClientId
    alias: str
    normalized_alias: str
    created_at: datetime
    updated_at: datetime
