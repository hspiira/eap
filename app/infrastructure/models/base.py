"""
Base SQLAlchemy Model and Mixins

Provides common functionality for all database models.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, DeclarativeBase
from sqlalchemy.sql import func

from app.shared.utils.generators import generate_cuid

class Base(DeclarativeBase):
    pass


class CuidMixin:
    """Mixin for models using CUID as primary key."""

    @declared_attr
    def id(cls) -> Mapped[str]:
        return mapped_column(String, primary_key=True, default=generate_cuid)


class TenantMixin:
    """Mixin for multi-tenant models."""

    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        return mapped_column(
            String,
            ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


class TimestampMixin:
    """Mixin for timestamp tracking (created_at, updated_at)."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality (deleted_at)."""

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(DateTime(timezone=True), nullable=True, index=True)
