"""Eligible-member use cases.

Creating an eligible member always creates a paired ``ClinicalSubject`` and the
audited link in one transactional unit. The pseudonym is generated server-side
and never derived from PII so the privacy wall holds even if the link table is
later compromised in isolation.
"""

from __future__ import annotations

from datetime import date

from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberGender, MemberRelation
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
)
from app.domain.services.pseudonymisation import generate_pseudonym
from app.domain.value_objects.core import (
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    Email,
    TenantId,
    UserId,
)
from app.domain.value_objects.staffing import EmploymentDetails
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class EnrolEligibleMemberUseCase:
    def __init__(
        self,
        member_repository: EligibleMemberRepository,
        subject_repository: ClinicalSubjectRepository,
        link_repository: EligibleMemberClinicalLinkRepository,
    ):
        self._members = member_repository
        self._subjects = subject_repository
        self._links = link_repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        client_id: ClientId,
        employer_member_id: str,
        relation: MemberRelation,
        tenant_secret: str,
        created_by: UserId | None = None,
        primary_employee_member_id: EligibleMemberId | None = None,
        import_source_id: str | None = None,
        coverage_start: date | None = None,
        coverage_end: date | None = None,
        work_email: Email | None = None,
        personal_email: Email | None = None,
        display_label: str | None = None,
        date_of_birth: date | None = None,
        gender: MemberGender | None = None,
        phone: str | None = None,
        staff_number: str | None = None,
        national_id: str | None = None,
        passport_number: str | None = None,
        employment: EmploymentDetails | None = None,
    ) -> tuple[EligibleMember, ClinicalSubject]:
        existing = await self._members.find_by_employer_member_id(
            tenant_id, client_id, employer_member_id
        )
        if existing is not None:
            raise DomainError(
                f"Eligible member already exists for employer_member_id={employer_member_id}"
            )
        if import_source_id is not None:
            existing_source = await self._members.find_by_import_source_id(
                tenant_id, client_id, import_source_id
            )
            if existing_source is not None:
                raise DomainError(
                    f"Eligible member already exists for import_source_id={import_source_id}"
                )
        now = utc_now()
        member = EligibleMember(
            id=EligibleMemberId(generate_cuid()),
            tenant_id=tenant_id,
            client_id=client_id,
            employer_member_id=employer_member_id,
            relation=relation,
            status=EligibilityStatus.ACTIVE,
            primary_employee_member_id=primary_employee_member_id,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            work_email=work_email,
            personal_email=personal_email,
            display_label=display_label,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            staff_number=staff_number,
            import_source_id=import_source_id,
            national_id=national_id,
            passport_number=passport_number,
            employment=employment,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        member.record_created()
        await self._members.save(member)

        subject = ClinicalSubject(
            id=ClinicalSubjectId(generate_cuid()),
            tenant_id=tenant_id,
            pseudonym=generate_pseudonym(tenant_secret=tenant_secret),
            created_at=now,
            updated_at=now,
        )
        await self._subjects.save(subject)

        await self._links.link(
            tenant_id=tenant_id,
            member_id=member.id,
            subject_id=subject.id,
        )
        return member, subject


class ResolveClinicalSubjectUseCase:
    """Privacy-wall checkpoint: only clinical-scope callers receive the mapping."""

    def __init__(
        self,
        link_repository: EligibleMemberClinicalLinkRepository,
    ):
        self._links = link_repository

    async def for_member(
        self,
        *,
        tenant_id: TenantId,
        member_id: EligibleMemberId,
        requester_id: str,
        purpose: str,
    ) -> ClinicalSubjectId:
        if not purpose:
            raise DomainError("purpose is required when resolving a clinical subject")
        subject_id = await self._links.subject_for_member(
            tenant_id,
            member_id,
            requester_id=requester_id,
            purpose=purpose,
        )
        if subject_id is None:
            raise NotFoundError(
                f"No clinical subject linked to member {member_id.value}",
                resource_type="ClinicalSubject",
                resource_id=member_id.value,
            )
        return subject_id
