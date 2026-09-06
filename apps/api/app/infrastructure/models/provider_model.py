"""Independent provider/practitioner persistence."""

from sqlalchemy import JSON, ForeignKeyConstraint, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import BaseStatus, ProviderIdentityProvenance
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ProviderModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "providers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_providers_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_providers_user_tenant",
            ondelete="RESTRICT",
        ),
        Index(
            "uq_providers_tenant_user_link",
            "tenant_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
    )

    user_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    identity_provenance: Mapped[ProviderIdentityProvenance] = mapped_column(
        EnumValueType(ProviderIdentityProvenance),
        nullable=False,
        default=ProviderIdentityProvenance.OWNED,
    )
    status: Mapped[BaseStatus] = mapped_column(
        EnumValueType(BaseStatus),
        nullable=False,
        default=BaseStatus.PENDING,
    )
    license_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provider_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
