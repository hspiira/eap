"""
Tenant SQLAlchemy Model

Database representation of Tenant aggregate.
This is a data container only - no business logic.
"""

from sqlalchemy import CheckConstraint, Enum as SQLEnum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SubscriptionTier, TenantStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class TenantModel(CuidMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Tenant aggregate.

    This is a data container for persistence only.
    Business logic lives in TenantEntity.
    """

    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            f"status IN {tuple([e.value for e in TenantStatus])}",
            name="tenant_status_check",
        ),
        CheckConstraint(
            f"subscription_tier IN {tuple([e.value for e in SubscriptionTier])}",
            name="tenant_subscription_tier_check",
        ),
    )

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    status: Mapped[TenantStatus] = mapped_column(
        SQLEnum(TenantStatus), nullable=False, default=TenantStatus.ACTIVE
    )

    # Configuration
    # Store TenantSettings as JSON since it's a value object
    settings: Mapped[dict] = mapped_column(JSON, nullable=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE
    )

    def __repr__(self) -> str:
        return f"<TenantModel(id={self.id}, name={self.name}, code={self.code})>"
