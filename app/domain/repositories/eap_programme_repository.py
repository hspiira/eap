"""EAP programme + Authorization repository ports."""

from app.domain.entities.authorization import Authorization
from app.domain.entities.eap_programme import EAPProgramme
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ContractId,
    EAPProgrammeId,
    TenantId,
)


class EAPProgrammeRepository(BaseRepository[EAPProgramme, EAPProgrammeId]):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 50
    ) -> list[EAPProgramme]:
        ...

    async def list_for_contract(
        self, tenant_id: TenantId, contract_id: ContractId
    ) -> list[EAPProgramme]:
        ...


class AuthorizationRepository(BaseRepository[Authorization, AuthorizationId]):
    async def list_for_case(
        self, tenant_id: TenantId, case_id: CaseId
    ) -> list[Authorization]:
        ...
