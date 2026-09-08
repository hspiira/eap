"""Clinical case use cases.

The Case aggregate is the orchestration spine for one episode of care. The
``OpenCaseUseCase`` is the only path that creates Cases; it always resolves
the supplied ``EligibleMemberId`` to its pseudonymous ``ClinicalSubjectId``
through the audited link repository, so a Case can never be opened directly
against employer-side identifiers.
"""

from __future__ import annotations

from app.application.use_cases.base import BaseUseCase
from app.application.use_cases.eligible_member_use_cases import (
    ResolveClinicalSubjectUseCase,
)
from app.domain.entities.case import Case
from app.domain.entities.clinical_note import ClinicalNote
from app.domain.enums import (
    AccessScope,
    CaseClosureReason,
    CaseStatus,
    ClinicalNoteType,
)
from app.domain.exceptions import DomainError, InvalidStateError, NotFoundError
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.clinical_note_repository import ClinicalNoteRepository
from app.domain.repositories.eligible_member_repository import (
    EligibleMemberClinicalLinkRepository,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.clinical_note_body import NarrativeBody
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalNoteId,
    EligibleMemberId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class OpenCaseUseCase(BaseUseCase[Case, CaseId]):
    def __init__(
        self,
        repository: CaseRepository,
        link_repository: EligibleMemberClinicalLinkRepository,
    ):
        super().__init__(repository)
        self._resolver = ResolveClinicalSubjectUseCase(link_repository)

    async def execute(
        self,
        *,
        case_id: CaseId,
        tenant_id: TenantId,
        client_id: ClientId,
        member_id: EligibleMemberId,
        presenting_problem: str,
        referral_source: str,
        opened_by: UserId,
        referral_notes: str | None = None,
    ) -> Case:
        subject_id = await self._resolver.for_member(
            tenant_id=tenant_id,
            member_id=member_id,
            requester_id=opened_by.value,
            purpose="open_case",
        )
        now = utc_now()
        case = Case(
            id=case_id,
            tenant_id=tenant_id,
            clinical_subject_id=subject_id,
            client_id=client_id,
            presenting_problem=presenting_problem,
            referral_source=referral_source,
            status=CaseStatus.INTAKE,
            opened_at=now,
            referred_by_user_id=opened_by,
            referral_notes=referral_notes,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(case)


class AssignCounsellorUseCase:
    def __init__(self, repository: CaseRepository, user_repository: UserRepository):
        self._repo = repository
        self._users = user_repository

    async def execute(
        self, *, case_id: CaseId, counsellor_id: PersonId, tenant_id: TenantId
    ) -> Case:
        case = await self._repo.get_by_id(case_id)
        if case is None:
            raise NotFoundError(
                f"Case not found: {case_id.value}",
                resource_type="Case",
                resource_id=case_id.value,
            )
        counsellor = await self._users.get_by_id(UserId(counsellor_id.value))
        if (
            counsellor is None
            or counsellor.tenant_id.value != tenant_id.value
            or AccessScope.CLINICAL not in counsellor.access_scopes
        ):
            raise DomainError(
                "counsellor_id must reference a user with Clinical access in this tenant"
            )
        case.assign_counsellor(counsellor_id)
        await self._repo.save(case)
        return case


class AdvanceCaseStatusUseCase:
    def __init__(self, repository: CaseRepository):
        self._repo = repository

    async def execute(self, *, case_id: CaseId, target: CaseStatus) -> Case:
        case = await self._repo.get_by_id(case_id)
        if case is None:
            raise NotFoundError(
                f"Case not found: {case_id.value}",
                resource_type="Case",
                resource_id=case_id.value,
            )
        case.advance(target)
        await self._repo.save(case)
        return case


class CloseCaseUseCase:
    def __init__(self, repository: CaseRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        case_id: CaseId,
        reason: CaseClosureReason,
        closure_summary_note_id: str | None = None,
    ) -> Case:
        case = await self._repo.get_by_id(case_id)
        if case is None:
            raise NotFoundError(
                f"Case not found: {case_id.value}",
                resource_type="Case",
                resource_id=case_id.value,
            )
        case.close(reason=reason, closure_summary_note_id=closure_summary_note_id)
        await self._repo.save(case)
        return case


class ReferOutCaseUseCase:
    def __init__(self, repository: CaseRepository, note_repository: ClinicalNoteRepository):
        self._repo = repository
        self._notes = note_repository

    async def execute(
        self, *, case_id: CaseId, notes: str, referred_by: UserId, tenant_id: TenantId
    ) -> Case:
        if not notes:
            raise DomainError("refer_out requires explanatory notes")
        case = await self._repo.get_by_id(case_id)
        if case is None or case.tenant_id.value != tenant_id.value:
            raise NotFoundError(
                f"Case not found: {case_id.value}",
                resource_type="Case",
                resource_id=case_id.value,
            )
        if case.is_terminal():
            raise InvalidStateError(f"Cannot refer out a {case.status.value} case")
        now = utc_now()
        note = ClinicalNote(
            id=ClinicalNoteId(generate_cuid()),
            tenant_id=case.tenant_id,
            case_id=case.id,
            clinical_subject_id=case.clinical_subject_id,
            note_type=ClinicalNoteType.CLOSURE_SUMMARY,
            body=NarrativeBody(summary=notes).as_dict(),
            author_id=referred_by,
            created_at=now,
            updated_at=now,
        )
        await self._notes.save(note)
        case.refer_out(closure_summary_note_id=note.id.value)
        await self._repo.save(case)
        return case
