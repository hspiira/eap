"""
Client SQLAlchemy Model

Database representation of Client aggregate.
This is a data container only - no business logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import BaseStatus, ClientTier, ContactMethod
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)

if TYPE_CHECKING:
    from app.infrastructure.models.client_alias_model import ClientAliasModel


class ClientModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Client aggregate.

    This is a data container for persistence only.
    Business logic lives in ClientEntity.
    """

    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{e.value}'" for e in BaseStatus) + ")",
            name="client_status_check",
        ),
        CheckConstraint(
            "preferred_contact_method IS NULL OR preferred_contact_method IN ("
            + ", ".join(f"'{e.value}'" for e in ContactMethod)
            + ")",
            name="client_contact_method_check",
        ),
    )

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(
        String(5), nullable=False, index=True
    )  # 3-5 character unique code
    contact_info: Mapped[dict] = mapped_column(JSON, nullable=False)
    billing_address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    alias_records: Mapped[list[ClientAliasModel]] = relationship(
        back_populates="client", cascade="all, delete-orphan", lazy="selectin"
    )

    # Relationships
    industry_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    parent_client_id: Mapped[str | None] = mapped_column(
        ForeignKey("clients.id"), nullable=True, index=True
    )

    # Status - use native PG enum (create_type=False) so PostgreSQL accepts the type
    status: Mapped[BaseStatus] = mapped_column(
        Enum(
            BaseStatus,
            name="basestatus",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=BaseStatus.PENDING,
    )
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    preferred_contact_method: Mapped[ContactMethod | None] = mapped_column(
        Enum(
            ContactMethod,
            name="contactmethod",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )
    tier: Mapped[ClientTier | None] = mapped_column(
        EnumValueType(ClientTier), nullable=True, index=True
    )
    suspension_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<ClientModel(id={self.id}, name={self.name}, status={self.status})>"


Index(
    "uq_clients_tenant_name_active",
    ClientModel.tenant_id,
    func.lower(ClientModel.name),
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
    sqlite_where=text("deleted_at IS NULL"),
)
Index(
    "uq_clients_tenant_code_active",
    ClientModel.tenant_id,
    func.upper(ClientModel.code),
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
    sqlite_where=text("deleted_at IS NULL"),
)
