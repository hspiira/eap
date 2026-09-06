"""Provider repository port."""

from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.domain.entities.provider import ProviderEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
)
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ProviderId, TenantId, UserId

SORTABLE_FIELDS = ("display_name", "created_at", "updated_at")


@dataclass(frozen=True)
class ProviderListQuery:
    """Server-side directory query. Filters apply to the whole tenant dataset."""

    search: str | None = None
    tiers: tuple[ProviderTier, ...] = ()
    regions: tuple[UgandaRegion, ...] = ()
    panel_statuses: tuple[PanelStatus, ...] = ()
    accreditation_statuses: tuple[AccreditationStatus, ...] = ()
    statuses: tuple[BaseStatus, ...] = field(default_factory=tuple)
    has_account: bool | None = None
    sort_by: str = "display_name"
    sort_desc: bool = False
    page: int = 1
    limit: int = 50

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class ProviderRepository(BaseRepository[ProviderEntity, ProviderId]):
    @abstractmethod
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ProviderEntity]: ...

    @abstractmethod
    async def count(self, tenant_id: TenantId) -> int: ...

    @abstractmethod
    async def search(
        self, tenant_id: TenantId, query: ProviderListQuery
    ) -> Sequence[ProviderEntity]: ...

    @abstractmethod
    async def count_matching(self, tenant_id: TenantId, query: ProviderListQuery) -> int: ...

    @abstractmethod
    async def get_for_booking(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> ProviderEntity | None:
        """Read a practitioner for a write path, locking the row.

        Booking validates eligibility inside its own transaction. Locking the
        row serialises it against a concurrent lifecycle change, so a preview
        that has since been invalidated cannot authorise the write.
        """
        ...

    @abstractmethod
    async def get_by_user_id(
        self, tenant_id: TenantId, user_id: UserId
    ) -> ProviderEntity | None: ...

    @abstractmethod
    async def get_user_in_tenant(
        self, user_id: UserId, tenant_id: TenantId
    ) -> UserEntity | None: ...

    @abstractmethod
    async def get_users_in_tenant(
        self, user_ids: Sequence[UserId], tenant_id: TenantId
    ) -> dict[str, UserEntity]: ...
