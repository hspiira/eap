"""Clinical note repository port."""

from app.domain.entities.clinical_note import ClinicalNote
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    TenantId,
)


class ClinicalNoteRepository(BaseRepository[ClinicalNote, ClinicalNoteId]):
    async def list_for_case(
        self, tenant_id: TenantId, case_id: CaseId
    ) -> list[ClinicalNote]:
        ...
