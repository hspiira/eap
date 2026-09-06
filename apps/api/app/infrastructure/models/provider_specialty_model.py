"""Global specialty catalogue and tenant-owned practitioner links (decision 5)."""

from sqlalchemy import Boolean, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    TenantMixin,
    TimestampMixin,
)


class ProviderSpecialtyModel(CuidMixin, Base, TimestampMixin):
    """Shared vocabulary. Carries no tenant_id by design."""

    __tablename__ = "provider_specialties"
    __table_args__ = (UniqueConstraint("code", name="uq_provider_specialties_code"),)

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


class ProviderSpecialtyLinkModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """A tenant's assertion that its practitioner holds a global specialty."""

    __tablename__ = "provider_specialty_links"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider_id",
            "specialty_id",
            name="uq_provider_specialty_links_tenant_provider_specialty",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_specialty_links_tenant_provider",
            ondelete="CASCADE",
        ),
    )

    provider_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    specialty_id: Mapped[str] = mapped_column(
        String(25),
        ForeignKey("provider_specialties.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
