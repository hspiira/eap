"""
Person SQLAlchemy Model

Database representation of Person aggregate.
This is a data container only - no business logic.
"""

from datetime import date

from sqlalchemy import CheckConstraint, Enum as SQLEnum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import BaseStatus, PersonType
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class PersonModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Person aggregate.

    This is a data container for persistence only.
    Business logic lives in PersonEntity.
    """

    __tablename__ = "persons"
    __table_args__ = (
        CheckConstraint(
            f"person_type IN {tuple([e.value for e in PersonType])}",
            name="person_type_check",
        ),
        CheckConstraint(
            f"secondary_person_type IN {tuple([e.value for e in PersonType])}",
            name="person_secondary_type_check",
        ),
        CheckConstraint(
            f"status IN {tuple([e.value for e in BaseStatus])}",
            name="person_status_check",
        ),
    )

    # Type discriminator
    person_type: Mapped[PersonType] = mapped_column(
        SQLEnum(PersonType, native_enum=False), nullable=False
    )
    is_dual_role: Mapped[bool] = mapped_column(default=False, nullable=False)
    secondary_person_type: Mapped[PersonType | None] = mapped_column(
        SQLEnum(PersonType, native_enum=False), nullable=True
    )

    # Core relationships
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Type-specific info (stored as JSON value objects)
    employment_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    license_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    staff_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dependent_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Shared
    status: Mapped[BaseStatus] = mapped_column(
        SQLEnum(BaseStatus, native_enum=False), nullable=False, default=BaseStatus.PENDING
    )
    emergency_contact: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_service_date: Mapped[date | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<PersonModel(id={self.id}, person_type={self.person_type}, user_id={self.user_id})>"
