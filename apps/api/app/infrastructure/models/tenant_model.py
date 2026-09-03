"""
Tenant SQLAlchemy Model

Database representation of Tenant aggregate.
This is a data container only - no business logic.
"""

from sqlalchemy import JSON, Boolean, CheckConstraint, Enum, String
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
    # Use native PostgreSQL enum type (create_type=False). values_callable so we send
    # enum value ("Active") not name ("ACTIVE") to match the DB enum labels.
    status: Mapped[TenantStatus] = mapped_column(
        Enum(
            TenantStatus,
            name="tenantstatus",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=TenantStatus.ACTIVE,
    )

    # Configuration
    # Store TenantSettings as JSON since it's a value object
    settings: Mapped[dict] = mapped_column(JSON, nullable=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(
            SubscriptionTier,
            name="subscriptiontier",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=SubscriptionTier.FREE,
    )

    # Azure SSO
    azure_tenant_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, unique=True, index=True
    )
    azure_sso_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    def __repr__(self) -> str:
        return f"<TenantModel(id={self.id}, name={self.name}, code={self.code})>"
