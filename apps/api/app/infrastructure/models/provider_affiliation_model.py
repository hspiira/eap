"""Provider affiliation persistence.

Composite foreign keys carry the tenant into both parents, so the database
rejects a cross-tenant affiliation without relying on application checks
(decision 3).
"""

from datetime import date

from sqlalchemy import Date, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    TenantMixin,
    TimestampMixin,
)


class ProviderAffiliationModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "provider_affiliations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "id", "provider_id", name="uq_provider_affiliations_tenant_provider"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_affiliations_tenant_provider",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "organisation_id"],
            ["provider_organisations.tenant_id", "provider_organisations.id"],
            name="fk_provider_affiliations_tenant_organisation",
            ondelete="RESTRICT",
        ),
    )

    provider_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    organisation_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
