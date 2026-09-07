"""Database model for the practitioner engagement-document checklist."""

from sqlalchemy import ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import EngagementDocumentKind, EngagementDocumentState
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class ProviderEngagementDocumentModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "provider_engagement_documents"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider_id",
            "document_kind",
            name="uq_provider_engagement_documents_kind",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_engagement_documents_provider_tenant",
            ondelete="CASCADE",
        ),
    )

    provider_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    document_kind: Mapped[EngagementDocumentKind] = mapped_column(
        EnumValueType(EngagementDocumentKind), nullable=False
    )
    state: Mapped[EngagementDocumentState] = mapped_column(
        EnumValueType(EngagementDocumentState), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
