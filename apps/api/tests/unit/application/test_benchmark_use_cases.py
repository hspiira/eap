"""Cross-tenant benchmark use case tests (Phase 4 #D-Benchmark)."""

from datetime import UTC, datetime

import pytest

from app.application.use_cases.benchmark_use_cases import (
    GetCrossTenantBenchmarkUseCase,
    GrantBenchmarkConsentUseCase,
    WithdrawBenchmarkConsentUseCase,
)
from app.domain.entities.benchmark_consent import BenchmarkConsent
from app.domain.enums import BenchmarkScope, TenantConsentStatus
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
    UserId,
)


def _consent(tenant_id: str, scope: BenchmarkScope) -> BenchmarkConsent:
    now = datetime.now(UTC)
    return BenchmarkConsent(
        id=BenchmarkConsentId(f"c-{tenant_id}"),
        tenant_id=TenantId(tenant_id),
        scope=scope,
        status=TenantConsentStatus.ACTIVE,
        version="v1",
        granted_by=UserId("u-admin"),
        granted_at=now,
        created_at=now,
        updated_at=now,
    )


class _FakeConsentRepo:
    def __init__(self, *consents: BenchmarkConsent):
        self.store: dict[str, BenchmarkConsent] = {c.id.value: c for c in consents}

    async def get_by_id(self, cid):
        return self.store.get(cid.value)

    async def save(self, entity):
        self.store[entity.id.value] = entity

    async def delete(self, cid):
        self.store.pop(cid.value, None)

    async def exists(self, cid):
        return cid.value in self.store

    async def list_for_tenant(self, tenant_id):
        return [c for c in self.store.values() if c.tenant_id == tenant_id]

    async def list_active_for_scope(self, scope):
        return [
            c
            for c in self.store.values()
            if c.scope == scope and c.status == TenantConsentStatus.ACTIVE
        ]

    async def find_active_for_tenant_scope(self, tenant_id, scope):
        for c in self.store.values():
            if (
                c.tenant_id == tenant_id
                and c.scope == scope
                and c.status == TenantConsentStatus.ACTIVE
            ):
                return c
        return None


class _FakeCollector:
    def __init__(self, per_tenant: dict[str, float]):
        self.per_tenant = per_tenant

    async def per_tenant_values(self, *, tenant_ids, scope, from_date, to_date) -> dict[str, float]:
        ids = {t.value for t in tenant_ids}
        return {tid: v for tid, v in self.per_tenant.items() if tid in ids}


# ---------- Grant + withdraw ----------


class TestGrantConsent:
    @pytest.mark.asyncio
    async def test_grants_new_consent(self):
        repo = _FakeConsentRepo()
        out = await GrantBenchmarkConsentUseCase(repo).execute(
            consent_id=BenchmarkConsentId("c-1"),
            tenant_id=TenantId("t-1"),
            scope=BenchmarkScope.SESSION_VOLUME,
            version="2026-05",
            granted_by=UserId("u-admin"),
        )
        assert out.is_currently_consented()

    @pytest.mark.asyncio
    async def test_rejects_duplicate_active_consent(self):
        existing = _consent("t-1", BenchmarkScope.SESSION_VOLUME)
        repo = _FakeConsentRepo(existing)
        with pytest.raises(DomainError, match="Active consent already exists"):
            await GrantBenchmarkConsentUseCase(repo).execute(
                consent_id=BenchmarkConsentId("c-2"),
                tenant_id=TenantId("t-1"),
                scope=BenchmarkScope.SESSION_VOLUME,
                version="2026-06",
                granted_by=UserId("u-admin"),
            )


class TestWithdrawConsent:
    @pytest.mark.asyncio
    async def test_withdraws_active(self):
        c = _consent("t-1", BenchmarkScope.SESSION_VOLUME)
        repo = _FakeConsentRepo(c)
        out = await WithdrawBenchmarkConsentUseCase(repo).execute(
            consent_id=BenchmarkConsentId("c-t-1"),
            actor=UserId("u-admin"),
            reason="reset for new TOS",
        )
        assert out.status == TenantConsentStatus.WITHDRAWN

    @pytest.mark.asyncio
    async def test_unknown_consent_404(self):
        repo = _FakeConsentRepo()
        with pytest.raises(NotFoundError):
            await WithdrawBenchmarkConsentUseCase(repo).execute(
                consent_id=BenchmarkConsentId("ghost"),
                actor=UserId("u-admin"),
                reason="x",
            )


# ---------- Cross-tenant aggregate ----------


class TestCrossTenantBenchmark:
    @pytest.mark.asyncio
    async def test_suppressed_below_floor(self):
        # Only 3 consenting tenants, well below default k=10
        repo = _FakeConsentRepo(
            *(_consent(f"t-{i}", BenchmarkScope.SESSION_VOLUME) for i in range(3))
        )
        collector = _FakeCollector(per_tenant={f"t-{i}": float(i + 1) for i in range(3)})
        out = await GetCrossTenantBenchmarkUseCase(repo, collector).execute(
            scope=BenchmarkScope.SESSION_VOLUME,
            metric_code="completed_session_count",
        )
        assert out.suppressed is True
        assert out.contributor_count == 3
        assert out.value is None

    @pytest.mark.asyncio
    async def test_discloses_at_floor(self):
        repo = _FakeConsentRepo(
            *(_consent(f"t-{i}", BenchmarkScope.SESSION_VOLUME) for i in range(10))
        )
        collector = _FakeCollector(per_tenant={f"t-{i}": 5.0 for i in range(10)})
        out = await GetCrossTenantBenchmarkUseCase(repo, collector).execute(
            scope=BenchmarkScope.SESSION_VOLUME,
            metric_code="completed_session_count",
        )
        assert out.suppressed is False
        assert out.contributor_count == 10
        assert out.value["mean"] == 5.0

    @pytest.mark.asyncio
    async def test_overridden_floor_for_test_fixture(self):
        repo = _FakeConsentRepo(
            *(_consent(f"t-{i}", BenchmarkScope.SATISFACTION) for i in range(3))
        )
        collector = _FakeCollector(per_tenant={f"t-{i}": float(i) for i in range(3)})
        out = await GetCrossTenantBenchmarkUseCase(repo, collector, floor=3).execute(
            scope=BenchmarkScope.SATISFACTION, metric_code="satisfaction_proxy"
        )
        assert out.suppressed is False

    @pytest.mark.asyncio
    async def test_no_consenting_tenants_yields_zero_contributors(self):
        out = await GetCrossTenantBenchmarkUseCase(_FakeConsentRepo(), _FakeCollector({})).execute(
            scope=BenchmarkScope.SESSION_VOLUME, metric_code="x"
        )
        assert out.contributor_count == 0
        assert out.suppressed is True

    @pytest.mark.asyncio
    async def test_withdrawn_consent_excluded(self):
        active = _consent("t-1", BenchmarkScope.SESSION_VOLUME)
        withdrawn = _consent("t-2", BenchmarkScope.SESSION_VOLUME)
        withdrawn.withdraw(actor=UserId("u-admin"), reason="x")
        repo = _FakeConsentRepo(active, withdrawn)
        collector = _FakeCollector(per_tenant={"t-1": 1.0, "t-2": 99.0})
        out = await GetCrossTenantBenchmarkUseCase(repo, collector, floor=1).execute(
            scope=BenchmarkScope.SESSION_VOLUME, metric_code="x"
        )
        # Only active tenant contributes:
        assert out.contributor_count == 1
        assert out.value["mean"] == 1.0
