"""Benchmark-consent model (Phase 4 #D-Benchmark)."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import BenchmarkScope, TenantConsentStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class BenchmarkConsentModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "benchmark_consents"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "scope",
            "version",
            name="uq_benchmark_consent_tenant_scope_version",
        ),
    )

    scope: Mapped[BenchmarkScope] = mapped_column(
        EnumValueType(BenchmarkScope), nullable=False, index=True
    )
    status: Mapped[TenantConsentStatus] = mapped_column(
        EnumValueType(TenantConsentStatus),
        nullable=False,
        default=TenantConsentStatus.ACTIVE,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    granted_by: Mapped[str] = mapped_column(String(25), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    withdrawn_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
