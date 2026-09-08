"""Utilisation event repository port (Phase 2 #D-Pricing)."""

from datetime import date

from app.domain.entities.utilisation_event import UtilisationEventEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    ContractId,
    TenantId,
    UtilisationEventId,
)


class UtilisationEventRepository(BaseRepository[UtilisationEventEntity, UtilisationEventId]):
    async def list_for_contract(
        self,
        tenant_id: TenantId,
        contract_id: ContractId,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[UtilisationEventEntity]: ...

    async def list_for_client(
        self,
        tenant_id: TenantId,
        client_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[UtilisationEventEntity]: ...

    async def count_for_client(self, tenant_id: TenantId, client_id: str) -> int: ...
