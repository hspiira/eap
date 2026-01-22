"""
ClientTag SQLAlchemy Model

Database representation of ClientTag aggregate.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ClientTagModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """SQLAlchemy Model for ClientTag aggregate."""

    __tablename__ = "client_tags"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<ClientTagModel(id={self.id}, name={self.name})>"
