"""Benchmark-consent mapper (Phase 4 #D-Benchmark)."""

from app.domain.entities.benchmark_consent import BenchmarkConsent
from app.domain.enums import BenchmarkScope, TenantConsentStatus
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
    UserId,
)
from app.infrastructure.models.benchmark_consent_model import (
    BenchmarkConsentModel,
)
from app.shared.utils.datetime import ensure_utc


class BenchmarkConsentMapper:
    @staticmethod
    def to_entity(model: BenchmarkConsentModel) -> BenchmarkConsent:
        entity = BenchmarkConsent(
            id=BenchmarkConsentId(model.id),
            tenant_id=TenantId(model.tenant_id),
            scope=BenchmarkScope(model.scope),
            status=TenantConsentStatus(model.status),
            version=model.version,
            granted_by=UserId(model.granted_by),
            granted_at=ensure_utc(model.granted_at),
            withdrawn_at=ensure_utc(model.withdrawn_at)
            if model.withdrawn_at
            else None,
            withdrawn_by=UserId(model.withdrawn_by)
            if model.withdrawn_by
            else None,
            withdrawn_reason=model.withdrawn_reason,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: BenchmarkConsent) -> BenchmarkConsentModel:
        return BenchmarkConsentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            scope=entity.scope,
            status=entity.status,
            version=entity.version,
            granted_by=entity.granted_by.value,
            granted_at=ensure_utc(entity.granted_at),
            withdrawn_at=ensure_utc(entity.withdrawn_at)
            if entity.withdrawn_at
            else None,
            withdrawn_by=entity.withdrawn_by.value
            if entity.withdrawn_by
            else None,
            withdrawn_reason=entity.withdrawn_reason,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
