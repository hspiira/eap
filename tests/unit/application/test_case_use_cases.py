"""Case lifecycle use case tests (refer-out and assign-counsellor)."""

from datetime import UTC, datetime

import pytest

from app.application.use_cases.case_use_cases import (
    AssignCounsellorUseCase,
    ReferOutCaseUseCase,
)
from app.domain.entities.case import Case
from app.domain.entities.clinical_note import ClinicalNote
from app.domain.entities.user import UserEntity
from app.domain.enums import (
    AccessScope,
    CaseReferralSource,
    CaseStatus,
    ClinicalNoteType,
    PresentingProblem,
    UserStatus,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalSubjectId,
    Email,
    PersonId,
    TenantId,
    UserId,
)


def _case(*, tenant_id: str = "t-1", referral_notes: str | None = None) -> Case:
    now = datetime.now(UTC)
    return Case(
        id=CaseId("case-1"),
        tenant_id=TenantId(tenant_id),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        client_id=ClientId("client-1"),
        presenting_problem=PresentingProblem.STRESS,
        referral_source=CaseReferralSource.SELF,
        status=CaseStatus.INTAKE,
        opened_at=now,
        referral_notes=referral_notes,
        created_at=now,
        updated_at=now,
    )


def _user(*, user_id: str, tenant_id: str = "t-1", scopes: list[AccessScope] | None = None) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        id=UserId(user_id),
        tenant_id=TenantId(tenant_id),
        email=Email(f"{user_id}@example.test"),
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
        access_scopes=scopes or [],
    )


class _FakeCaseRepo:
    def __init__(self):
        self.store: dict[str, Case] = {}

    async def get_by_id(self, cid):
        return self.store.get(cid.value)

    async def save(self, c):
        self.store[c.id.value] = c

    async def delete(self, cid):
        self.store.pop(cid.value, None)

    async def exists(self, cid):
        return cid.value in self.store


class _FakeNoteRepo:
    def __init__(self):
        self.store: dict[str, ClinicalNote] = {}

    async def get_by_id(self, nid):
        return self.store.get(nid.value)

    async def save(self, n):
        self.store[n.id.value] = n

    async def delete(self, nid):
        self.store.pop(nid.value, None)

    async def exists(self, nid):
        return nid.value in self.store


class _FakeUserRepo:
    def __init__(self, users: list[UserEntity]):
        self.store = {u.id.value: u for u in users}

    async def get_by_id(self, uid):
        return self.store.get(uid.value)


class TestReferOutCaseUseCase:
    @pytest.mark.asyncio
    async def test_creates_a_closure_summary_note_and_preserves_referral_notes(self):
        cases = _FakeCaseRepo()
        notes = _FakeNoteRepo()
        cases.store["case-1"] = _case(referral_notes="Referred by HR due to conduct concerns")
        use_case = ReferOutCaseUseCase(cases, notes)

        result = await use_case.execute(
            case_id=CaseId("case-1"),
            notes="Client requires specialised substance-use care; referring externally.",
            referred_by=UserId("counsellor-1"),
        )

        assert result.status == CaseStatus.REFERRED_OUT
        assert result.referral_notes == "Referred by HR due to conduct concerns"
        assert result.closure_summary_note_id is not None
        saved_note = notes.store[result.closure_summary_note_id]
        assert saved_note.note_type == ClinicalNoteType.CLOSURE_SUMMARY
        assert saved_note.author_id == UserId("counsellor-1")
        assert "substance-use" in saved_note.body["summary"]

    @pytest.mark.asyncio
    async def test_requires_notes(self):
        cases = _FakeCaseRepo()
        cases.store["case-1"] = _case()
        use_case = ReferOutCaseUseCase(cases, _FakeNoteRepo())
        with pytest.raises(DomainError, match="notes"):
            await use_case.execute(case_id=CaseId("case-1"), notes="", referred_by=UserId("u-1"))

    @pytest.mark.asyncio
    async def test_unknown_case_404s(self):
        use_case = ReferOutCaseUseCase(_FakeCaseRepo(), _FakeNoteRepo())
        with pytest.raises(NotFoundError):
            await use_case.execute(
                case_id=CaseId("ghost"), notes="notes", referred_by=UserId("u-1")
            )


class TestAssignCounsellorUseCase:
    @pytest.mark.asyncio
    async def test_assigns_a_clinical_scoped_user(self):
        cases = _FakeCaseRepo()
        cases.store["case-1"] = _case()
        users = _FakeUserRepo([_user(user_id="counsellor-1", scopes=[AccessScope.CLINICAL])])
        use_case = AssignCounsellorUseCase(cases, users)

        result = await use_case.execute(
            case_id=CaseId("case-1"),
            counsellor_id=PersonId("counsellor-1"),
            tenant_id=TenantId("t-1"),
        )
        assert result.assigned_counsellor_id == PersonId("counsellor-1")

    @pytest.mark.asyncio
    async def test_rejects_a_user_without_clinical_scope(self):
        cases = _FakeCaseRepo()
        cases.store["case-1"] = _case()
        users = _FakeUserRepo([_user(user_id="hr-user", scopes=[])])
        use_case = AssignCounsellorUseCase(cases, users)

        with pytest.raises(DomainError, match="Clinical access"):
            await use_case.execute(
                case_id=CaseId("case-1"),
                counsellor_id=PersonId("hr-user"),
                tenant_id=TenantId("t-1"),
            )

    @pytest.mark.asyncio
    async def test_rejects_a_user_from_another_tenant(self):
        cases = _FakeCaseRepo()
        cases.store["case-1"] = _case(tenant_id="t-1")
        users = _FakeUserRepo(
            [_user(user_id="other-tenant-user", tenant_id="t-2", scopes=[AccessScope.CLINICAL])]
        )
        use_case = AssignCounsellorUseCase(cases, users)

        with pytest.raises(DomainError, match="Clinical access"):
            await use_case.execute(
                case_id=CaseId("case-1"),
                counsellor_id=PersonId("other-tenant-user"),
                tenant_id=TenantId("t-1"),
            )

    @pytest.mark.asyncio
    async def test_rejects_an_unknown_counsellor_id(self):
        cases = _FakeCaseRepo()
        cases.store["case-1"] = _case()
        use_case = AssignCounsellorUseCase(cases, _FakeUserRepo([]))

        with pytest.raises(DomainError, match="Clinical access"):
            await use_case.execute(
                case_id=CaseId("case-1"),
                counsellor_id=PersonId("ghost"),
                tenant_id=TenantId("t-1"),
            )
