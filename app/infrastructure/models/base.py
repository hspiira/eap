"""
Base SQLAlchemy Model and Mixins

Provides common functionality for all database models.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.sql import func

from app.shared.utils.generators import generate_cuid


class Base(DeclarativeBase):
    pass


class EnumValueType(TypeDecorator):
    """
    Custom type decorator that ensures enum values (not names) are stored.

    For string enums, SQLAlchemy's Enum type may use enum names instead of values.
    This decorator ensures we always store the enum value.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        """Convert enum to its value when storing in database."""
        if value is None:
            return None
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, str):
            # If it's already a string, validate it's a valid enum value
            try:
                enum_obj = self.enum_class(value)
                return enum_obj.value
            except ValueError:
                # If value doesn't match, try by name
                try:
                    enum_obj = getattr(self.enum_class, value)
                    return enum_obj.value
                except AttributeError as e:
                    raise ValueError(f"Invalid {self.enum_class.__name__} value: {value!r}") from e
        return value

    def process_result_value(self, value, dialect):
        """Convert database value back to enum object."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value
        return self.enum_class(value)


class CuidMixin:
    """Mixin for models using CUID as primary key."""

    @declared_attr
    def id(cls) -> Mapped[str]:
        return mapped_column(String(25), primary_key=True, default=generate_cuid)


class TenantMixin:
    """Mixin for multi-tenant models."""

    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        return mapped_column(
            String(25),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


class TimestampMixin:
    """Mixin for timestamp tracking (created_at, updated_at)."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

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
