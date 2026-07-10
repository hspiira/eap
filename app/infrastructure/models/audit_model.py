"""
Audit SQLAlchemy Models

Database representation of Audit aggregates.
These are data containers only - no business logic.
Audit logs are immutable - no updates or deletes.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import AuditActionType
from app.infrastructure.models.base import Base, CuidMixin, TenantMixin, TimestampMixin


class AuditLogModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """
    SQLAlchemy Model for AuditLog aggregate.

    This is a data container for persistence only.
    Business logic lives in AuditLog entity.
    Audit logs are immutable - no updates or deletes.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "action_type IN (" + ", ".join(f"'{e.value}'" for e in AuditActionType) + ")",
            name="audit_action_type_check",
        ),
    )

    # User reference
    user_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )

    # Action details
    action_type: Mapped[AuditActionType] = mapped_column(
        String(50), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )

    # Description and context
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )  # Column name is 'metadata' in DB, attribute is 'extra_metadata' in Python

    occurred_at: Mapped[datetime] = mapped_column(
        nullable=False, index=True
    )

    is_special_category: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false", index=True
    )

    entity_changes: Mapped[list["EntityChangeModel"]] = relationship(
        "EntityChangeModel",
        back_populates="audit_log",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AuditLogModel(id={self.id}, action_type={self.action_type}, resource_type={self.resource_type})>"


class EntityChangeModel(CuidMixin, Base, TimestampMixin):
    """
    SQLAlchemy Model for EntityChange aggregate.

    This is a data container for persistence only.
    Business logic lives in EntityChange entity.
    Entity changes are immutable - no updates or deletes.
    """

    __tablename__ = "entity_changes"

    # Reference to audit log
    audit_log_id: Mapped[str] = mapped_column(
        ForeignKey("audit_logs.id"), nullable=False, index=True
    )

    # Entity reference
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    entity_id: Mapped[str] = mapped_column(
        String(25), nullable=False, index=True
    )

    # Field changes stored as JSON array
    field_changes: Mapped[list[dict]] = mapped_column(JSON, nullable=False)

    # Relationship to audit log
    audit_log: Mapped["AuditLogModel"] = relationship(
        "AuditLogModel", back_populates="entity_changes"
    )

    def __repr__(self) -> str:
        return f"<EntityChangeModel(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id})>"
