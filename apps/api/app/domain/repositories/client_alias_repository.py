"""Repository contract for tenant-scoped client aliases."""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.client_alias import ClientAliasEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientAliasId, ClientId, TenantId


class ClientAliasRepository(BaseRepository[ClientAliasEntity, ClientAliasId]):
    """Persistence operations for alternate client names."""

    @abstractmethod
    async def list_for_client(
        self, client_id: ClientId, tenant_id: TenantId
    ) -> Sequence[ClientAliasEntity]:
        """List aliases belonging to a client."""

    @abstractmethod
    async def find_by_normalized(
        self, tenant_id: TenantId, normalized_alias: str
    ) -> ClientAliasEntity | None:
        """Find the owner of a normalized alias."""

    @abstractmethod
    async def replace_for_client(
        self, client_id: ClientId, tenant_id: TenantId, aliases: Sequence[str]
    ) -> Sequence[ClientAliasEntity]:
        """Replace a client's aliases atomically."""

    @abstractmethod
    async def merge_into(
        self, target_client_id: ClientId, source_client_id: ClientId, tenant_id: TenantId
    ) -> Sequence[ClientAliasEntity]:
        """Move source aliases to target, dropping normalized duplicates."""
