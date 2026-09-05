"""Eligible-member + clinical-subject repository ports."""

from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    TenantId,
)


class EligibleMemberRepository(BaseRepository[EligibleMember, EligibleMemberId]):
    async def list_for_client(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[EligibleMember]: ...

    async def list_for_primary(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        primary_employee_member_id: EligibleMemberId,
        *,
        limit: int = 100,
    ) -> list[EligibleMember]: ...

    async def list_all(
        self,
        tenant_id: TenantId,
        *,
        client_id: ClientId | None = None,
        status: EligibilityStatus | None = None,
        relation: MemberRelation | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> list[EligibleMember]: ...

    async def count(
        self,
        tenant_id: TenantId,
        *,
        client_id: ClientId | None = None,
        status: EligibilityStatus | None = None,
        relation: MemberRelation | None = None,
        search: str | None = None,
    ) -> int: ...

    async def find_by_employer_member_id(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        employer_member_id: str,
    ) -> EligibleMember | None: ...

    async def next_member_sequence(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        prefix: str,
    ) -> int:
        """Next free numeric suffix for ``{prefix}-###`` member ids in this client."""
        ...


class ClinicalSubjectRepository(BaseRepository[ClinicalSubject, ClinicalSubjectId]):
    async def find_by_pseudonym(
        self, tenant_id: TenantId, pseudonym: str
    ) -> ClinicalSubject | None: ...


class EligibleMemberClinicalLinkRepository:
    """Audited 1:1 mapping between EligibleMember and ClinicalSubject.

    Implemented separately from the two aggregates because *every* read of this
    table is a privacy event that must be logged as such (special-category-data
    access). The repository is the only structural join site.
    """

    async def link(
        self,
        *,
        tenant_id: TenantId,
        member_id: EligibleMemberId,
        subject_id: ClinicalSubjectId,
    ) -> None: ...

    async def subject_for_member(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId,
        *,
        requester_id: str,
        purpose: str,
    ) -> ClinicalSubjectId | None: ...

    async def member_for_subject(
        self,
        tenant_id: TenantId,
        subject_id: ClinicalSubjectId,
        *,
        requester_id: str,
        purpose: str,
    ) -> EligibleMemberId | None: ...
