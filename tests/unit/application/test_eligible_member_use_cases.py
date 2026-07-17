"""EnrolEligibleMember use case + privacy-wall resolver tests."""

import logging

import pytest

from app.application.use_cases.eligible_member_use_cases import (
    EnrolEligibleMemberUseCase,
    ResolveClinicalSubjectUseCase,
)
from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import MemberRelation
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import (
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    TenantId,
)

SECRET = "tenant-pseudonym-secret-of-ample-length"


class _FakeMemberRepo:
    def __init__(self):
        self.store: dict[str, EligibleMember] = {}

    async def get_by_id(self, mid):
        return self.store.get(mid.value)

    async def save(self, m):
        self.store[m.id.value] = m

    async def delete(self, mid):
        self.store.pop(mid.value, None)

    async def exists(self, mid):
        return mid.value in self.store

    async def list_for_client(self, tenant_id, client_id, *, limit=200, offset=0):
        return [
            m
            for m in self.store.values()
            if m.tenant_id == tenant_id and m.client_id == client_id
        ]

    async def find_by_employer_member_id(
        self, tenant_id, client_id, employer_member_id
    ):
        for m in self.store.values():
            if (
                m.tenant_id == tenant_id
                and m.client_id == client_id
                and m.employer_member_id == employer_member_id
            ):
                return m
        return None


class _FakeSubjectRepo:
    def __init__(self):
        self.store: dict[str, ClinicalSubject] = {}

    async def get_by_id(self, sid):
        return self.store.get(sid.value)

    async def save(self, s):
        self.store[s.id.value] = s

    async def delete(self, sid):
        self.store.pop(sid.value, None)

    async def exists(self, sid):
        return sid.value in self.store

    async def find_by_pseudonym(self, tenant_id, pseudonym):
        for s in self.store.values():
            if s.tenant_id == tenant_id and s.pseudonym == pseudonym:
                return s
        return None


class _FakeLinkRepo:
    def __init__(self):
        self.member_to_subject: dict[str, str] = {}
        self.disclosure_log: list[dict] = []

    async def link(self, *, tenant_id, member_id, subject_id):
        self.member_to_subject[member_id.value] = subject_id.value

    async def subject_for_member(
        self, tenant_id, member_id, *, requester_id, purpose
    ):
        sid = self.member_to_subject.get(member_id.value)
        self.disclosure_log.append(
            {
                "direction": "member_to_subject",
                "requester": requester_id,
                "purpose": purpose,
                "found": sid is not None,
            }
        )
        return ClinicalSubjectId(sid) if sid else None

    async def member_for_subject(
        self, tenant_id, subject_id, *, requester_id, purpose
    ):
        for mid, sid in self.member_to_subject.items():
            if sid == subject_id.value:
                self.disclosure_log.append(
                    {
                        "direction": "subject_to_member",
                        "requester": requester_id,
                        "purpose": purpose,
                        "found": True,
                    }
                )
                return EligibleMemberId(mid)
        self.disclosure_log.append(
            {
                "direction": "subject_to_member",
                "requester": requester_id,
                "purpose": purpose,
                "found": False,
            }
        )
        return None


class TestEnrolEligibleMember:
    @pytest.mark.asyncio
    async def test_creates_member_subject_and_link(self):
        members, subjects, links = (
            _FakeMemberRepo(),
            _FakeSubjectRepo(),
            _FakeLinkRepo(),
        )
        use_case = EnrolEligibleMemberUseCase(members, subjects, links)
        member, subject = await use_case.execute(
            tenant_id=TenantId("t-1"),
            client_id=ClientId("c-1"),
            employer_member_id="HR-001",
            relation=MemberRelation.EMPLOYEE,
            tenant_secret=SECRET,
        )
        assert member.employer_member_id == "HR-001"
        assert subject.pseudonym.startswith("cs_")
        assert links.member_to_subject[member.id.value] == subject.id.value

    @pytest.mark.asyncio
    async def test_duplicate_employer_id_rejected(self):
        members, subjects, links = (
            _FakeMemberRepo(),
            _FakeSubjectRepo(),
            _FakeLinkRepo(),
        )
        use_case = EnrolEligibleMemberUseCase(members, subjects, links)
        await use_case.execute(
            tenant_id=TenantId("t-1"),
            client_id=ClientId("c-1"),
            employer_member_id="HR-001",
            relation=MemberRelation.EMPLOYEE,
            tenant_secret=SECRET,
        )
        with pytest.raises(DomainError, match="already exists"):
            await use_case.execute(
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                employer_member_id="HR-001",
                relation=MemberRelation.EMPLOYEE,
                tenant_secret=SECRET,
            )


class TestResolveClinicalSubject:
    @pytest.mark.asyncio
    async def test_resolves_and_logs_purpose(self, caplog):
        members, subjects, links = (
            _FakeMemberRepo(),
            _FakeSubjectRepo(),
            _FakeLinkRepo(),
        )
        member, subject = await EnrolEligibleMemberUseCase(
            members, subjects, links
        ).execute(
            tenant_id=TenantId("t-1"),
            client_id=ClientId("c-1"),
            employer_member_id="HR-1",
            relation=MemberRelation.EMPLOYEE,
            tenant_secret=SECRET,
        )
        resolver = ResolveClinicalSubjectUseCase(links)
        with caplog.at_level(logging.INFO):
            sid = await resolver.for_member(
                tenant_id=TenantId("t-1"),
                member_id=member.id,
                requester_id="clinician-1",
                purpose="open_case",
            )
        assert sid == subject.id
        assert links.disclosure_log[0]["purpose"] == "open_case"

    @pytest.mark.asyncio
    async def test_purpose_required(self):
        resolver = ResolveClinicalSubjectUseCase(_FakeLinkRepo())
        with pytest.raises(DomainError, match="purpose"):
            await resolver.for_member(
                tenant_id=TenantId("t-1"),
                member_id=EligibleMemberId("em-1"),
                requester_id="clinician-1",
                purpose="",
            )

    @pytest.mark.asyncio
    async def test_unknown_member_404(self):
        resolver = ResolveClinicalSubjectUseCase(_FakeLinkRepo())
        with pytest.raises(NotFoundError):
            await resolver.for_member(
                tenant_id=TenantId("t-1"),
                member_id=EligibleMemberId("ghost"),
                requester_id="clinician-1",
                purpose="open_case",
            )
