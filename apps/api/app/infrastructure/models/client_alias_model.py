"""SQLAlchemy model for normalized client aliases."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base, CuidMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.models.client_model import ClientModel


class ClientAliasModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """A unique alternate client name within a tenant."""

    __tablename__ = "client_aliases"
    __table_args__ = (
        Index("uq_client_aliases_tenant_normalized", "tenant_id", "normalized_alias", unique=True),
    )

    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client: Mapped[ClientModel] = relationship(back_populates="alias_records")
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False)
