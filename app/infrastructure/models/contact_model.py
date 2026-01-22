"""
Contact SQLAlchemy Model

Database representation of Contact aggregate.
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ContactModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """SQLAlchemy Model for Contact aggregate."""

    __tablename__ = "contacts"

    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<ContactModel(id={self.id}, name={self.name}, client_id={self.client_id})>"
