"""Practitioner alias persistence, scoped by tenant and source system."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.provider_network import AliasResolutionState
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class ProviderAliasModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "provider_aliases"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "normalized_value",
            name="uq_provider_aliases_tenant_source_normalized",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_aliases_tenant_provider",
            ondelete="RESTRICT",
        ),
    )

    source_system: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_value: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    state: Mapped[AliasResolutionState] = mapped_column(
        EnumValueType(AliasResolutionState),
        nullable=False,
        default=AliasResolutionState.UNMAPPED,
        index=True,
    )
    provider_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    candidate_provider_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
