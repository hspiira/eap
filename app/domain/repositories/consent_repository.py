"""Consent + DataSharingRegister + DPOContact repository ports."""

from app.domain.entities.consent import Consent
from app.domain.entities.data_sharing_register import DataSharingRegisterEntry
from app.domain.entities.dpo_contact import DPOContact
from app.domain.enums import ConsentPurpose, ConsentScope
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    ClinicalSubjectId,
    ConsentId,
    DataSharingRegisterEntryId,
    DPOContactId,
    TenantId,
)


class ConsentRepository(BaseRepository[Consent, ConsentId]):
    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[Consent]:
        ...

    async def find_active_for_disclosure(
        self,
        tenant_id: TenantId,
        subject_id: ClinicalSubjectId,
        *,
        scope: ConsentScope,
        purpose: ConsentPurpose,
        disclosure_to: str,
    ) -> Consent | None:
        ...


class DataSharingRegisterRepository(
    BaseRepository[DataSharingRegisterEntry, DataSharingRegisterEntryId]
):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 200
    ) -> list[DataSharingRegisterEntry]:
        ...

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[DataSharingRegisterEntry]:
        ...


class DPOContactRepository(BaseRepository[DPOContact, DPOContactId]):
    async def current_for_tenant(
        self, tenant_id: TenantId
    ) -> DPOContact | None:
        ...

    async def list_for_tenant(
        self, tenant_id: TenantId
    ) -> list[DPOContact]:
        ...
