"""Crisis contact repository port."""

from app.domain.entities.crisis_contact import CrisisContact
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    TenantId,
)


class CrisisContactRepository(BaseRepository[CrisisContact, CrisisContactId]):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[CrisisContact]: ...

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[CrisisContact]: ...

    async def list_for_case(self, tenant_id: TenantId, case_id: CaseId) -> list[CrisisContact]: ...
