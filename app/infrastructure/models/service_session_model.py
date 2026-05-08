"""
Service Session SQLAlchemy Model

Database representation of Service Session aggregate.
This is a data container only - no business logic.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SessionStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ServiceSessionModel(
    CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin
):
    """
    SQLAlchemy Model for Service Session aggregate.

    This is a data container for persistence only.
    Business logic lives in ServiceSessionEntity.
    """

    __tablename__ = "service_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{e.value}'" for e in SessionStatus) + ")",
            name="session_status_check",
        ),
    )

    # Relationships
    service_id: Mapped[str] = mapped_column(
        String(25), nullable=False, index=True
    )
    provider_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id"), nullable=False, index=True
    )
    person_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id"), nullable=False, index=True
    )

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        EnumValueType(SessionStatus), nullable=False, default=SessionStatus.SCHEDULED
    )
    reschedule_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Completion
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Details
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Optional link to a CISM critical-incident response
    incident_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<ServiceSessionModel(id={self.id}, status={self.status}, scheduled_at={self.scheduled_at})>"
