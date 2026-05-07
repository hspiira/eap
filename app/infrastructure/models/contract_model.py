"""
Contract SQLAlchemy Model

Database representation of Contract aggregate.
This is a data container only - no business logic.
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ContractModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Contract aggregate.

    This is a data container for persistence only.
    Business logic lives in ContractEntity.
    """

    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{e.value}'" for e in ContractStatus) + ")",
            name="contract_status_check",
        ),
        CheckConstraint(
            "payment_frequency IN (" + ", ".join(f"'{e.value}'" for e in PaymentFrequency) + ")",
            name="contract_payment_frequency_check",
        ),
        CheckConstraint(
            "payment_status IN (" + ", ".join(f"'{e.value}'" for e in PaymentStatus) + ")",
            name="contract_payment_status_check",
        ),
    )

    # Relationships
    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id"), nullable=False, index=True
    )

    # Contract period (stored as JSON)
    period: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Billing (stored as JSON)
    billing_rate: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Payment configuration - use native PG enums (create_type=False)
    payment_frequency: Mapped[PaymentFrequency] = mapped_column(
        Enum(
            PaymentFrequency,
            name="paymentfrequency",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="paymentstatus",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    # Status
    status: Mapped[ContractStatus] = mapped_column(
        Enum(
            ContractStatus,
            name="contractstatus",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ContractStatus.DRAFT,
    )
    is_auto_renew: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Billing dates
    last_billing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_billing_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Signing
    signed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Termination
    termination_reason: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ContractModel(id={self.id}, client_id={self.client_id}, status={self.status})>"
