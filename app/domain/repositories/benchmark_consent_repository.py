"""Benchmark-consent repository port (Phase 4 #D-Benchmark)."""

from app.domain.entities.benchmark_consent import BenchmarkConsent
from app.domain.enums import BenchmarkScope
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
)


class BenchmarkConsentRepository(BaseRepository[BenchmarkConsent, BenchmarkConsentId]):
    async def list_for_tenant(self, tenant_id: TenantId) -> list[BenchmarkConsent]: ...

    async def list_active_for_scope(self, scope: BenchmarkScope) -> list[BenchmarkConsent]: ...

    async def find_active_for_tenant_scope(
        self, tenant_id: TenantId, scope: BenchmarkScope
    ) -> BenchmarkConsent | None: ...
