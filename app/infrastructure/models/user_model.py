"""
User SQLAlchemy Model

Database representation of User aggregate.
This is a data container only - no business logic.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import Language, TenantRole, UserStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class UserModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for User aggregate.

    This is a data container for persistence only.
    Business logic lives in UserEntity.
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{e.value}'" for e in UserStatus) + ")",
            name="user_status_check",
        ),
        CheckConstraint(
            "preferred_language IN (" + ", ".join(f"'{e.value}'" for e in Language) + ")",
            name="user_language_check",
        ),
        CheckConstraint(
            "role IN (" + ", ".join(f"'{e.value}'" for e in TenantRole) + ")",
            name="user_role_check",
        ),
    )

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Status - native PG enum (userstatus); use value not name
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            name="userstatus",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
    )
    status_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Preferences - native PG enum (language)
    preferred_language: Mapped[Language | None] = mapped_column(
        Enum(
            Language,
            name="language",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # RBAC: role within tenant
    role: Mapped[TenantRole] = mapped_column(
        EnumValueType(TenantRole), nullable=False, default=TenantRole.USER
    )

    # Security
    is_two_factor_enabled: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    failed_login_count: Mapped[int] = mapped_column(
        default=0, nullable=False, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, status={self.status})>"
