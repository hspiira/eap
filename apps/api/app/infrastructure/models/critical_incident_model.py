"""Critical Incident model (Phase 2 #D-CISM)."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import CriticalIncidentSeverity, CriticalIncidentStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class CriticalIncidentModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """Aggregate row for a critical incident response."""

    __tablename__ = "critical_incidents"

    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[CriticalIncidentSeverity] = mapped_column(
        EnumValueType(CriticalIncidentSeverity), nullable=False, index=True
    )
    affected_population_size: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    logged_by: Mapped[str] = mapped_column(String(25), nullable=False)
    status: Mapped[CriticalIncidentStatus] = mapped_column(
        EnumValueType(CriticalIncidentStatus),
        nullable=False,
        default=CriticalIncidentStatus.OPEN,
        index=True,
    )
    phases: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default="[]")
    after_action_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
