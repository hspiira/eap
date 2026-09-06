"""
Service Session SQLAlchemy Model

Database representation of Service Session aggregate.
This is a data container only - no business logic.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    ClientType,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ServiceSessionModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
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
        CheckConstraint(
            "session_type IS NULL OR session_type IN ("
            + ", ".join(f"'{e.value}'" for e in SessionType)
            + ")",
            name="session_type_check",
        ),
        CheckConstraint(
            "category IS NULL OR category IN ("
            + ", ".join(f"'{e.value}'" for e in SessionCategory)
            + ")",
            name="session_category_check",
        ),
        CheckConstraint(
            "client_type IS NULL OR client_type IN ("
            + ", ".join(f"'{e.value}'" for e in ClientType)
            + ")",
            name="session_client_type_check",
        ),
        CheckConstraint(
            "clinical_outcome IS NULL OR clinical_outcome IN ("
            + ", ".join(f"'{e.value}'" for e in SessionClinicalStatus)
            + ")",
            name="session_clinical_outcome_check",
        ),
    )

    # Relationships
    service_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"), nullable=False, index=True)
    member_id: Mapped[str] = mapped_column(
        ForeignKey("eligible_members.id"), nullable=False, index=True
    )

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        EnumValueType(SessionStatus), nullable=False, default=SessionStatus.SCHEDULED
    )
    reschedule_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Completion
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Details
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Optional link to a CISM critical-incident response
    incident_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)

    # Phase 4 #D-Import: idempotency key for re-runnable historical loads.
    # Unique per tenant; absent for organic in-app sessions.
    import_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Care Activity Log fields
    session_type: Mapped[SessionType | None] = mapped_column(
        EnumValueType(SessionType), nullable=True, index=True
    )
    category: Mapped[SessionCategory | None] = mapped_column(
        EnumValueType(SessionCategory), nullable=True, index=True
    )
    rate_ugx: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issue_topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis_type_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    diagnosis_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    approved_by: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    session_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partner_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    partner_relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)
    headcount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_type: Mapped[ClientType | None] = mapped_column(
        EnumValueType(ClientType), nullable=True, index=True
    )
    clinical_outcome: Mapped[SessionClinicalStatus | None] = mapped_column(
        EnumValueType(SessionClinicalStatus), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<ServiceSessionModel(id={self.id}, status={self.status}, scheduled_at={self.scheduled_at})>"
