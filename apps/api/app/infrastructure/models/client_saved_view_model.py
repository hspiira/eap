"""SQLAlchemy model for shareable client list views."""

from sqlalchemy import JSON, Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, CuidMixin, TenantMixin, TimestampMixin


class ClientSavedViewModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """A named set of client-list filters owned by a tenant user."""

    __tablename__ = "client_saved_views"
    __table_args__ = (
        Index("ix_client_saved_views_tenant_created_by", "tenant_id", "created_by"),
        Index("ix_client_saved_views_tenant_shared", "tenant_id", "is_shared"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
