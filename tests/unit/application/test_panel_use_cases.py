"""Panel-management use case tests (Phase 4 #D-Provider)."""

from datetime import UTC, date, datetime

import pytest

from app.application.use_cases.panel_use_cases import (
    BulkUpdatePanelStatusUseCase,
    ChangeProviderTierUseCase,
    CheckProviderEligibilityUseCase,
)
from app.domain.entities.non_compete_clause import NonCompeteClauseEntity
from app.domain.entities.person import PersonEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import (
    AccreditationStatus,
    NonCompeteStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
    UserStatus,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import (
    ClientId,
    Email,
    LicenseInfo,
    NonCompeteClauseId,
    PersonId,
    ProviderProfile,
    TenantId,
    UserId,
)


def _user(uid: str = "u-1") -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        id=UserId(uid),
        tenant_id=TenantId("t-1"),
        email=Email(f"{uid}@example.com"),
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


def _profile(
    panel: PanelStatus = PanelStatus.ACTIVE,
    accred: AccreditationStatus = AccreditationStatus.ACCREDITED,
) -> ProviderProfile:
    return ProviderProfile(
        tier=ProviderTier.T2,
        region=UgandaRegion.CENTRAL,
        accreditation_status=accred,
        panel_status=panel,
    )


def _provider(
    pid: str = "prov-1",
    profile: ProviderProfile | None = None,
    *,
    tenant: str = "t-1",
) -> PersonEntity:
    person = PersonEntity.create_service_provider(
        id=PersonId(pid),
        tenant_id=TenantId(tenant),
        user_id=UserId("u-1"),
        profile=_user(),
        license_info=LicenseInfo(number="L", issuing_authority="UMC"),
    )
    if profile is not None:
        person.update_provider_profile(profile)
    return person


class _FakePersonRepo:
    def __init__(self, *people: PersonEntity):
        self.people = {p.id.value: p for p in people}

    async def get_by_id(self, pid):
        return self.people.get(pid.value)

    async def save(self, person):
        self.people[person.id.value] = person

    async def delete(self, pid):
        self.people.pop(pid.value, None)

    async def exists(self, pid):
        return pid.value in self.people


class _FakeClauseRepo:
    def __init__(self, clauses: list[NonCompeteClauseEntity] | None = None):
        self.clauses = clauses or []

    async def get_by_id(self, cid):
        for c in self.clauses:
            if c.id == cid:
                return c
        return None

    async def save(self, c):
        self.clauses.append(c)

    async def delete(self, cid):
        self.clauses = [c for c in self.clauses if c.id != cid]

    async def exists(self, cid):
        return any(c.id == cid for c in self.clauses)

    async def list_for_provider(self, tenant_id, provider_id):
        return [c for c in self.clauses if c.provider_id == provider_id]


# ---------- Bulk panel status ----------


class TestBulkUpdatePanelStatus:
    @pytest.mark.asyncio
    async def test_updates_active_providers(self):
        p1 = _provider("p1", _profile(panel=PanelStatus.ACTIVE))
        p2 = _provider("p2", _profile(panel=PanelStatus.ACTIVE))
        repo = _FakePersonRepo(p1, p2)
        result = await BulkUpdatePanelStatusUseCase(repo).execute(
            tenant_id=TenantId("t-1"),
            provider_ids=[PersonId("p1"), PersonId("p2")],
            new_status=PanelStatus.REMOVED,
            actor=UserId("admin"),
            reason="80→8 panel cull",
        )
        assert set(result.updated) == {"p1", "p2"}
        assert repo.people["p1"].provider_profile.panel_status == PanelStatus.REMOVED

    @pytest.mark.asyncio
    async def test_skips_unchanged_provider(self):
        p1 = _provider("p1", _profile(panel=PanelStatus.REMOVED))
        repo = _FakePersonRepo(p1)
        result = await BulkUpdatePanelStatusUseCase(repo).execute(
            tenant_id=TenantId("t-1"),
            provider_ids=[PersonId("p1")],
            new_status=PanelStatus.REMOVED,
            actor=UserId("admin"),
            reason="cull",
        )
        assert result.updated == []
        assert result.skipped_no_change == ["p1"]

    @pytest.mark.asyncio
    async def test_records_unknown_ids(self):
        repo = _FakePersonRepo()
        result = await BulkUpdatePanelStatusUseCase(repo).execute(
            tenant_id=TenantId("t-1"),
            provider_ids=[PersonId("ghost")],
            new_status=PanelStatus.REMOVED,
            actor=UserId("admin"),
            reason="x",
        )
        assert result.not_found == ["ghost"]

    @pytest.mark.asyncio
    async def test_records_non_providers(self):
        # Create a person without a provider profile
        person = PersonEntity.create_service_provider(
            id=PersonId("staff"),
            tenant_id=TenantId("t-1"),
            user_id=UserId("u-1"),
            profile=_user(),
            license_info=LicenseInfo(number="L", issuing_authority="UMC"),
        )
        # No provider_profile set
        repo = _FakePersonRepo(person)
        result = await BulkUpdatePanelStatusUseCase(repo).execute(
            tenant_id=TenantId("t-1"),
            provider_ids=[PersonId("staff")],
            new_status=PanelStatus.REMOVED,
            actor=UserId("admin"),
            reason="x",
        )
        assert result.not_provider == ["staff"]

    @pytest.mark.asyncio
    async def test_reason_required(self):
        repo = _FakePersonRepo()
        with pytest.raises(DomainError, match="reason"):
            await BulkUpdatePanelStatusUseCase(repo).execute(
                tenant_id=TenantId("t-1"),
                provider_ids=[PersonId("p")],
                new_status=PanelStatus.REMOVED,
                actor=UserId("admin"),
                reason="",
            )

    @pytest.mark.asyncio
    async def test_empty_ids_rejected(self):
        repo = _FakePersonRepo()
        with pytest.raises(DomainError, match="non-empty"):
            await BulkUpdatePanelStatusUseCase(repo).execute(
                tenant_id=TenantId("t-1"),
                provider_ids=[],
                new_status=PanelStatus.REMOVED,
                actor=UserId("admin"),
                reason="x",
            )


# ---------- Tier change ----------


class TestChangeProviderTier:
    @pytest.mark.asyncio
    async def test_changes_tier(self):
        p = _provider("p1", _profile())
        repo = _FakePersonRepo(p)
        out = await ChangeProviderTierUseCase(repo).execute(
            tenant_id=TenantId("t-1"),
            provider_id=PersonId("p1"),
            new_tier=ProviderTier.T1,
            actor=UserId("admin"),
            reason="annual review",
        )
        assert out.provider_profile.tier == ProviderTier.T1

    @pytest.mark.asyncio
    async def test_unknown_provider_404(self):
        repo = _FakePersonRepo()
        with pytest.raises(NotFoundError):
            await ChangeProviderTierUseCase(repo).execute(
                tenant_id=TenantId("t-1"),
                provider_id=PersonId("ghost"),
                new_tier=ProviderTier.T1,
                actor=UserId("admin"),
                reason="x",
            )


# ---------- Eligibility ----------


def _clause(*, status: NonCompeteStatus = NonCompeteStatus.ACTIVE) -> NonCompeteClauseEntity:
    now = datetime.now(UTC)
    return NonCompeteClauseEntity(
        id=NonCompeteClauseId("c-1"),
        tenant_id=TenantId("t-1"),
        provider_id=PersonId("p1"),
        status=status,
        terms_summary="No competing assignments outside the platform.",
        effective_from=date(2026, 1, 1),
        effective_until=date(2027, 1, 1),
        created_at=now,
        updated_at=now,
    )


class TestCheckProviderEligibility:
    @pytest.mark.asyncio
    async def test_panel_eligible_no_clauses(self):
        p = _provider("p1", _profile())
        repo = _FakePersonRepo(p)
        out = await CheckProviderEligibilityUseCase(repo, _FakeClauseRepo()).execute(
            tenant_id=TenantId("t-1"),
            provider_id=PersonId("p1"),
            client_id=ClientId("client-x"),
        )
        assert out["eligible"] is True
        assert out["panel_eligible"] is True
        assert out["binding_non_compete_count"] == 0

    @pytest.mark.asyncio
    async def test_blocked_when_panel_suspended(self):
        p = _provider("p1", _profile(panel=PanelStatus.SUSPENDED))
        repo = _FakePersonRepo(p)
        out = await CheckProviderEligibilityUseCase(repo, _FakeClauseRepo()).execute(
            tenant_id=TenantId("t-1"),
            provider_id=PersonId("p1"),
        )
        assert out["eligible"] is False
        assert out["panel_eligible"] is False
        assert any("Panel-ineligible" in r for r in out["reasons"])

    @pytest.mark.asyncio
    async def test_blocked_when_binding_clause_present(self):
        p = _provider("p1", _profile())
        repo = _FakePersonRepo(p)
        clauses = _FakeClauseRepo([_clause()])
        out = await CheckProviderEligibilityUseCase(repo, clauses).execute(
            tenant_id=TenantId("t-1"),
            provider_id=PersonId("p1"),
        )
        assert out["eligible"] is False
        assert out["binding_non_compete_count"] == 1

    @pytest.mark.asyncio
    async def test_ignores_revoked_clauses(self):
        p = _provider("p1", _profile())
        revoked = _clause(status=NonCompeteStatus.REVOKED)
        repo = _FakePersonRepo(p)
        clauses = _FakeClauseRepo([revoked])
        out = await CheckProviderEligibilityUseCase(repo, clauses).execute(
            tenant_id=TenantId("t-1"),
            provider_id=PersonId("p1"),
        )
        assert out["eligible"] is True

    @pytest.mark.asyncio
    async def test_unknown_provider_404(self):
        repo = _FakePersonRepo()
        with pytest.raises(NotFoundError):
            await CheckProviderEligibilityUseCase(repo, _FakeClauseRepo()).execute(
                tenant_id=TenantId("t-1"),
                provider_id=PersonId("ghost"),
            )
