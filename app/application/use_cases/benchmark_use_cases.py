"""Cross-tenant benchmarking use cases (Phase 4 #D-Benchmark / SAD A-19)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.benchmark_consent import BenchmarkConsent
from app.domain.enums import BenchmarkScope, TenantConsentStatus
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.benchmark_consent_repository import (
    BenchmarkConsentRepository,
)
from app.domain.services.k_anonymity import (
    K_ANON_FLOOR,
    BenchmarkResult,
    enforce_k_anonymity,
)
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


class GrantBenchmarkConsentUseCase(BaseUseCase[BenchmarkConsent, BenchmarkConsentId]):
    def __init__(self, repository: BenchmarkConsentRepository):
        super().__init__(repository)
        self._repo = repository

    async def execute(
        self,
        *,
        consent_id: BenchmarkConsentId,
        tenant_id: TenantId,
        scope: BenchmarkScope,
        version: str,
        granted_by: UserId,
    ) -> BenchmarkConsent:
        existing = await self._repo.find_active_for_tenant_scope(tenant_id, scope)
        if existing is not None:
            raise DomainError(
                f"Active consent already exists for {scope.value} "
                f"(version {existing.version}); withdraw it first or use a new version"
            )
        now = utc_now()
        consent = BenchmarkConsent(
            id=consent_id,
            tenant_id=tenant_id,
            scope=scope,
            status=TenantConsentStatus.ACTIVE,
            version=version,
            granted_by=granted_by,
            granted_at=now,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(consent)


class WithdrawBenchmarkConsentUseCase:
    def __init__(self, repository: BenchmarkConsentRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        consent_id: BenchmarkConsentId,
        actor: UserId,
        reason: str,
    ) -> BenchmarkConsent:
        consent = await self._repo.get_by_id(consent_id)
        if consent is None:
            raise NotFoundError(
                f"Benchmark consent not found: {consent_id.value}",
                resource_type="BenchmarkConsent",
                resource_id=consent_id.value,
            )
        consent.withdraw(actor=actor, reason=reason)
        await self._repo.save(consent)
        return consent


class _MetricCollector(Protocol):
    """Computes a numeric aggregate per consenting tenant for one metric."""

    async def per_tenant_values(
        self,
        *,
        tenant_ids: list[TenantId],
        scope: BenchmarkScope,
        from_date: datetime | None,
        to_date: datetime | None,
    ) -> dict[str, float]:
        """Map tenant_id.value → numeric contribution (e.g. session count).

        Tenants with zero contribution may be omitted; callers count
        ``len(...)`` for the k-anon decision.
        """
        ...


class GetCrossTenantBenchmarkUseCase:
    """Aggregate one metric across all consenting tenants under k-anon enforcement.

    Workflow:
        1. List active consents for the requested ``BenchmarkScope``.
        2. Ask the collector for per-tenant numeric contributions.
        3. Compute the cross-tenant aggregate (mean by default).
        4. Run the result through ``enforce_k_anonymity``: if fewer than the
           floor of distinct tenants contributed, the value is suppressed and
           the response carries a structured suppression reason.
    """

    def __init__(
        self,
        consents: BenchmarkConsentRepository,
        collector: _MetricCollector,
        floor: int = K_ANON_FLOOR,
    ):
        self._consents = consents
        self._collector = collector
        self._floor = floor

    async def execute(
        self,
        *,
        scope: BenchmarkScope,
        metric_code: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> BenchmarkResult:
        active_consents = await self._consents.list_active_for_scope(scope)
        consenting_tenants = [c.tenant_id for c in active_consents]
        per_tenant = await self._collector.per_tenant_values(
            tenant_ids=consenting_tenants,
            scope=scope,
            from_date=from_date,
            to_date=to_date,
        )
        contributors = {
            tid: v for tid, v in per_tenant.items() if v is not None
        }
        contributor_count = len(contributors)
        if contributor_count == 0:
            mean: Any = None
        else:
            mean = sum(contributors.values()) / contributor_count
        return enforce_k_anonymity(
            metric_code=metric_code,
            contributor_count=contributor_count,
            value={"mean": mean, "samples": contributor_count},
            floor=self._floor,
        )
