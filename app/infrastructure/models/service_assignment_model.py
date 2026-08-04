"""
ServiceAssignment SQLAlchemy Model

Database representation of ServiceAssignment aggregate.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import BaseStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ServiceAssignmentModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """SQLAlchemy Model for ServiceAssignment aggregate."""

    __tablename__ = "service_assignments"

    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), nullable=False, index=True)
    status: Mapped[BaseStatus] = mapped_column(
        EnumValueType(BaseStatus), nullable=False, default=BaseStatus.PENDING
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ServiceAssignmentModel(id={self.id}, service_id={self.service_id}, contract_id={self.contract_id})>"
