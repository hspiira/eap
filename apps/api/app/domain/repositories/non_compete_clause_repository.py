"""Non-compete clause repository port (Phase 2 #D-Provider)."""

from app.domain.entities.non_compete_clause import NonCompeteClauseEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    NonCompeteClauseId,
    ProviderId,
    TenantId,
)


class NonCompeteClauseRepository(BaseRepository[NonCompeteClauseEntity, NonCompeteClauseId]):
    async def list_for_provider(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> list[NonCompeteClauseEntity]: ...
