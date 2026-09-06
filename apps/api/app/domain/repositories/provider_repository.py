"""Provider repository port."""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.provider import ProviderEntity
from app.domain.entities.user import UserEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ProviderId, TenantId, UserId


class ProviderRepository(BaseRepository[ProviderEntity, ProviderId]):
    @abstractmethod
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ProviderEntity]: ...

    @abstractmethod
    async def count(self, tenant_id: TenantId) -> int: ...

    @abstractmethod
    async def get_user_in_tenant(
        self, user_id: UserId, tenant_id: TenantId
    ) -> UserEntity | None: ...

    @abstractmethod
    async def get_users_in_tenant(
        self, user_ids: Sequence[UserId], tenant_id: TenantId
    ) -> dict[str, UserEntity]: ...
