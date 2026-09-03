"""
Service SQLAlchemy Model

Database representation of Service aggregate.
This is a data container only - no business logic.
"""

from sqlalchemy import CheckConstraint, Integer, String
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


class ServiceModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Service aggregate.

    This is a data container for persistence only.
    Business logic lives in ServiceEntity.
    """

    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{e.value}'" for e in BaseStatus) + ")",
            name="service_status_check",
        ),
    )

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Status
    status: Mapped[BaseStatus] = mapped_column(
        EnumValueType(BaseStatus),
        nullable=False,
        default=BaseStatus.PENDING,
    )

    # Service details
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_group_service: Mapped[bool] = mapped_column(default=False, nullable=False)
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<ServiceModel(id={self.id}, name={self.name}, status={self.status})>"
