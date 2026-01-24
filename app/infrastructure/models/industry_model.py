"""
Industry SQLAlchemy Model

Database representation of Industry aggregate.
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


class IndustryModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """SQLAlchemy Model for Industry aggregate."""

    __tablename__ = "industries"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    parent_industry_id: Mapped[str | None] = mapped_column(
        ForeignKey("industries.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<IndustryModel(id={self.id}, name={self.name})>"
