"""Provider organisation persistence."""

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ProviderOrganisationModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "provider_organisations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_provider_organisations_tenant"),
        UniqueConstraint("tenant_id", "name", name="uq_provider_organisations_tenant_name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    approval_status: Mapped[OrganisationApprovalStatus] = mapped_column(
        EnumValueType(OrganisationApprovalStatus),
        nullable=False,
        default=OrganisationApprovalStatus.PENDING,
        index=True,
    )
