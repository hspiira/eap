"""Engagement model (Phase 4 #D-Engagement).

Deliverables and hours-log entries live as JSONB arrays on the parent row;
they are children of the aggregate and never queried independently, so the
relational overhead of separate tables is unwarranted in v1.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import EngagementStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class EngagementModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "engagements"

    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[EngagementStatus] = mapped_column(
        EnumValueType(EngagementStatus),
        nullable=False,
        default=EngagementStatus.DRAFT,
        index=True,
    )
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    deliverables: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    hours_log: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    created_by: Mapped[str] = mapped_column(String(25), nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invoiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
