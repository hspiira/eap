"""
Service Session SQLAlchemy Model

Database representation of Service Session aggregate.
This is a data container only - no business logic.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionDeliveryContext,
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
        ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_service_sessions_provider_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["clients.tenant_id", "clients.id"],
            name="fk_service_sessions_client_tenant",
            ondelete="RESTRICT",
        ),
        # The member must belong to the client the session is attributed to.
        # Enforced here as well as in the application, so a direct write cannot
        # attach one client's member to another client's session.
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "member_id"],
            [
                "eligible_members.tenant_id",
                "eligible_members.client_id",
                "eligible_members.id",
            ],
            name="fk_service_sessions_member_client_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "attendance IN (" + ", ".join(f"'{e.value}'" for e in SessionAttendance) + ")",
            name="session_attendance_check",
        ),
        CheckConstraint(
            "(attendance = 'CompanyWide') = (member_id IS NULL)",
            name="session_attendance_matches_member_check",
        ),
        CheckConstraint(
            "delivery_context IN ("
            + ", ".join(f"'{e.value}'" for e in SessionDeliveryContext)
            + ")",
            name="session_delivery_context_check",
        ),
        CheckConstraint(
            "(delivery_context = 'Organisation') = (provider_affiliation_id IS NOT NULL)",
            name="session_affiliation_matches_context_check",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "provider_affiliation_id", "provider_id"],
            [
                "provider_affiliations.tenant_id",
                "provider_affiliations.id",
                "provider_affiliations.provider_id",
            ],
            name="fk_service_sessions_affiliation_tenant_provider",
            ondelete="RESTRICT",
        ),
    )

    # Relationships
    service_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    delivery_context: Mapped[SessionDeliveryContext] = mapped_column(
        EnumValueType(SessionDeliveryContext),
        nullable=False,
        default=SessionDeliveryContext.UNKNOWN,
    )
    provider_affiliation_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    # Nullable: a session delivered outside any term, or for a client with no
    # contract on file, still happened and is still attributed to the client.
    contract_id: Mapped[str | None] = mapped_column(
        ForeignKey("contracts.id"), nullable=True, index=True
    )
    attendance: Mapped[SessionAttendance] = mapped_column(
        EnumValueType(SessionAttendance),
        nullable=False,
        default=SessionAttendance.INDIVIDUAL,
        index=True,
    )
    member_id: Mapped[str | None] = mapped_column(
        ForeignKey("eligible_members.id"), nullable=True, index=True
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
    #: The session this one was booked off the back of. A self-reference rather
    #: than a link to a case: both ends are employer-side, so it carries the
    #: scheduling fact without bridging to the pseudonymous clinical subject.
    follow_up_of_session_id: Mapped[str | None] = mapped_column(
        String(25),
        ForeignKey("service_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

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
