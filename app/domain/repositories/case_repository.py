"""Clinical case repository port."""

from app.domain.entities.case import Case
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    PersonId,
    TenantId,
)


class CaseRepository(BaseRepository[Case, CaseId]):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[Case]:
        ...

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[Case]:
        ...

    async def list_for_counsellor(
        self,
        tenant_id: TenantId,
        counsellor_id: PersonId,
        *,
        limit: int = 100,
    ) -> list[Case]:
        ...
