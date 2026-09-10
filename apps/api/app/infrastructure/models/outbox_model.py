"""Outbox event SQLAlchemy model (Phase 1 #C10).

Rows are inserted in the same database transaction as the action that
produced them; a separate worker process drains the table and dispatches
the events to consumers (audit, notify, report). Delivery is at-least-once
with exponential backoff.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, CuidMixin, TimestampMixin


class OutboxEventModel(CuidMixin, Base, TimestampMixin):
    """Outbox row representing a domain event awaiting downstream delivery."""

    __tablename__ = "outbox_events"
    __table_args__ = (
        Index(
            "ix_outbox_events_undelivered",
            "delivered_at",
            "created_at",
            postgresql_where="delivered_at IS NULL",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    """No foreign key: the queue carries the platform sentinel as well as real
    tenant ids, and matches what the migration created."""

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    aggregate_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aggregate_id: Mapped[str | None] = mapped_column(String(25), nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    delivery_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<OutboxEventModel(id={self.id}, type={self.event_type}, "
            f"delivered={self.delivered_at is not None})>"
        )
