"""Clinical case use cases.

The Case aggregate is the orchestration spine for one episode of care. The
``OpenCaseUseCase`` is the only path that creates Cases — it always resolves
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
from app.domain.enums import (
    CaseClosureReason,
    CaseReferralSource,
    CaseStatus,
    PresentingProblem,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.eligible_member_repository import (
    EligibleMemberClinicalLinkRepository,
)
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


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
        presenting_problem: PresentingProblem,
        referral_source: CaseReferralSource,
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


class OpenCaseForSubjectUseCase(BaseUseCase[Case, CaseId]):
    """Open a case directly against a known ``ClinicalSubjectId``.

    Used by clinical-side flows that already hold the pseudonym (e.g. a follow-
    up case spawned from a CrisisContact) and don't need a fresh resolution.
    """

    def __init__(self, repository: CaseRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        case_id: CaseId,
        tenant_id: TenantId,
        client_id: ClientId,
        clinical_subject_id: ClinicalSubjectId,
        presenting_problem: PresentingProblem,
        referral_source: CaseReferralSource,
        opened_by: UserId,
        referral_notes: str | None = None,
    ) -> Case:
        now = utc_now()
        case = Case(
            id=case_id,
            tenant_id=tenant_id,
            clinical_subject_id=clinical_subject_id,
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
    def __init__(self, repository: CaseRepository):
        self._repo = repository

    async def execute(
        self, *, case_id: CaseId, counsellor_id: PersonId
    ) -> Case:
        case = await self._repo.get_by_id(case_id)
        if case is None:
            raise NotFoundError(
                f"Case not found: {case_id.value}",
                resource_type="Case",
                resource_id=case_id.value,
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
        case.close(
            reason=reason, closure_summary_note_id=closure_summary_note_id
        )
        await self._repo.save(case)
        return case


class ReferOutCaseUseCase:
    def __init__(self, repository: CaseRepository):
        self._repo = repository

    async def execute(self, *, case_id: CaseId, notes: str) -> Case:
        if not notes:
            raise DomainError("refer_out requires explanatory notes")
        case = await self._repo.get_by_id(case_id)
        if case is None:
            raise NotFoundError(
                f"Case not found: {case_id.value}",
                resource_type="Case",
                resource_id=case_id.value,
            )
        case.refer_out(notes=notes)
        await self._repo.save(case)
        return case
