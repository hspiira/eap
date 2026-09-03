"""DSAR request repository port (Phase 4 #DSAR)."""

from app.domain.entities.dsar_request import DSARRequest
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
)


class DSARRequestRepository(BaseRepository[DSARRequest, DSARRequestId]):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[DSARRequest]: ...

    async def list_for_subject(
        self, tenant_id: TenantId, subject_person_id: PersonId
    ) -> list[DSARRequest]: ...
