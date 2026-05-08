"""Non-compete clause model (Phase 2 #D-Provider)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import NonCompeteStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class NonCompeteClauseModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """Non-compete clause attached to a provider."""

    __tablename__ = "non_compete_clauses"

    provider_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    status: Mapped[NonCompeteStatus] = mapped_column(
        EnumValueType(NonCompeteStatus),
        nullable=False,
        default=NonCompeteStatus.DRAFT,
        index=True,
    )
    terms_summary: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signed_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
