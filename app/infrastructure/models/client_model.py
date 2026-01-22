"""
Client SQLAlchemy Model

Database representation of Client aggregate.
This is a data container only - no business logic.
"""

from sqlalchemy import CheckConstraint, Enum as SQLEnum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import BaseStatus, ContactMethod
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ClientModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Client aggregate.

    This is a data container for persistence only.
    Business logic lives in ClientEntity.
    """

    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint(
            f"status IN {tuple([e.value for e in BaseStatus])}",
            name="client_status_check",
        ),
        CheckConstraint(
            f"preferred_contact_method IN {tuple([e.value for e in ContactMethod])}",
            name="client_contact_method_check",
        ),
    )

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_info: Mapped[dict] = mapped_column(JSON, nullable=False)
    billing_address: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    industry_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    parent_client_id: Mapped[str | None] = mapped_column(
        ForeignKey("clients.id"), nullable=True, index=True
    )

    # Status
    status: Mapped[BaseStatus] = mapped_column(
        SQLEnum(BaseStatus, native_enum=False), nullable=False, default=BaseStatus.PENDING
    )
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    preferred_contact_method: Mapped[ContactMethod | None] = mapped_column(
        SQLEnum(ContactMethod, native_enum=False), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ClientModel(id={self.id}, name={self.name}, status={self.status})>"
