"""SQLAlchemy model for assigning tags to clients."""

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, CuidMixin, TenantMixin, TimestampMixin


class ClientTagAssignmentModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """Tenant-scoped many-to-many client/tag assignment."""

    __tablename__ = "client_tag_assignments"
    __table_args__ = (
        Index(
            "uq_client_tag_assignments_client_tag", "tenant_id", "client_id", "tag_id", unique=True
        ),
    )

    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_id: Mapped[str] = mapped_column(
        ForeignKey("client_tags.id", ondelete="CASCADE"), nullable=False, index=True
    )
