"""
KPI SQLAlchemy Models

Database representation of KPI aggregates.
This is a data container only - no business logic.
"""

from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class KPIModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for KPI aggregate.

    This is a data container for persistence only.
    Business logic lives in KPIEntity.
    """

    __tablename__ = "kpis"

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), ForeignKey("kpi_categories.code"), nullable=False, index=True
    )
    measurement_unit: Mapped[str] = mapped_column(
        String(50), ForeignKey("kpi_measurement_units.code"), nullable=False
    )

    # Targets and thresholds
    target_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    threshold_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    threshold_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<KPIModel(id={self.id}, name={self.name}, category={self.category})>"


class KPIAssignmentModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for KPI Assignment aggregate.

    This is a data container for persistence only.
    Business logic lives in KPIAssignmentEntity.
    """

    __tablename__ = "kpi_assignments"
    __table_args__ = (
        CheckConstraint(
            "(client_id IS NOT NULL) OR (contract_id IS NOT NULL)",
            name="kpi_assignment_client_or_contract_check",
        ),
        CheckConstraint(
            "(client_id IS NULL) OR (contract_id IS NULL)",
            name="kpi_assignment_not_both_check",
        ),
    )

    # KPI reference
    kpi_id: Mapped[str] = mapped_column(ForeignKey("kpis.id"), nullable=False, index=True)

    # Associations - one of these must be set
    client_id: Mapped[str | None] = mapped_column(
        ForeignKey("clients.id"), nullable=True, index=True
    )
    contract_id: Mapped[str | None] = mapped_column(
        ForeignKey("contracts.id"), nullable=True, index=True
    )

    # Assignment-specific target (overrides KPI target if set)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<KPIAssignmentModel(id={self.id}, kpi_id={self.kpi_id})>"
