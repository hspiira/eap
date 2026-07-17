"""
Audit Repository Implementation

SQLAlchemy implementation of AuditRepository interface.

Security: Audit logs are append-only. The application code never updates or deletes
audit records. For defense in depth, the database user used by the app should have
only INSERT and SELECT on audit tables (no UPDATE/DELETE) so audit data cannot
be altered even if application code is compromised.
"""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.audit import AuditLog, EntityChange
from app.domain.enums import AuditActionType
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.value_objects.core import (
    AuditLogId,
    TenantId,
    UserId,
)
from app.infrastructure.mappers.audit_mapper import AuditMapper
from app.infrastructure.models.audit_model import AuditLogModel, EntityChangeModel


class AuditRepositoryImpl(AuditRepository):
    """
    SQLAlchemy implementation of AuditRepository.

    Handles data access for Audit aggregates.
    Uses mapper to convert between entity and model.
    Audit logs are immutable - no updates or deletes.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def save_audit_log(self, audit_log: AuditLog) -> None:
        """
        Save an audit log entry.

        Audit logs are immutable - this only inserts.
        """
        model = AuditMapper.to_audit_log_model(audit_log)
        self.session.add(model)
        # Note: commit is typically handled by the application service/unit of work

    async def save_entity_change(self, entity_change: EntityChange) -> None:
        """
        Save an entity change entry.

        Entity changes are immutable - this only inserts.
        """
        model = AuditMapper.to_entity_change_model(entity_change)
        self.session.add(model)
        # Note: commit is typically handled by the application service/unit of work

    async def get_audit_log_by_id(
        self, audit_log_id: AuditLogId
    ) -> AuditLog | None:
        """Get audit log by ID."""
        stmt = select(AuditLogModel).where(AuditLogModel.id == audit_log_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return AuditMapper.to_audit_log_entity(model)

    async def list_audit_logs(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        action_type: AuditActionType | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "occurred_at",
        sort_desc: bool = True,
    ) -> Sequence[AuditLog]:
        """List audit logs with filtering and pagination."""
        stmt = select(AuditLogModel).where(
            AuditLogModel.tenant_id == tenant_id.value
        )

        # Apply filters
        if user_id:
            stmt = stmt.where(AuditLogModel.user_id == user_id.value)
        if action_type:
            stmt = stmt.where(AuditLogModel.action_type == action_type)
        if resource_type:
            stmt = stmt.where(AuditLogModel.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(AuditLogModel.resource_id == resource_id)
        if start_date:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            stmt = stmt.where(AuditLogModel.occurred_at >= start_dt)
        if end_date:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            stmt = stmt.where(AuditLogModel.occurred_at <= end_dt)

        # Apply sorting
        sort_column = getattr(AuditLogModel, sort_by, AuditLogModel.occurred_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [AuditMapper.to_audit_log_entity(model) for model in models]

    async def count_audit_logs(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        action_type: AuditActionType | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> int:
        """Count audit logs matching filters."""
        stmt = select(func.count(AuditLogModel.id)).where(
            AuditLogModel.tenant_id == tenant_id.value
        )

        # Apply filters
        if user_id:
            stmt = stmt.where(AuditLogModel.user_id == user_id.value)
        if action_type:
            stmt = stmt.where(AuditLogModel.action_type == action_type)
        if resource_type:
            stmt = stmt.where(AuditLogModel.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(AuditLogModel.resource_id == resource_id)
        if start_date:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            stmt = stmt.where(AuditLogModel.occurred_at >= start_dt)
        if end_date:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            stmt = stmt.where(AuditLogModel.occurred_at <= end_dt)

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def get_entity_changes_by_audit_log_id(
        self, audit_log_id: AuditLogId
    ) -> Sequence[EntityChange]:
        """Get all entity changes for an audit log."""
        stmt = select(EntityChangeModel).where(
            EntityChangeModel.audit_log_id == audit_log_id.value
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [AuditMapper.to_entity_change_entity(model) for model in models]

    async def get_entity_changes_by_entity(
        self,
        tenant_id: TenantId,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[EntityChange]:
        """Get all entity changes for a specific entity."""
        # Join with audit_logs to filter by tenant
        stmt = (
            select(EntityChangeModel)
            .join(AuditLogModel, EntityChangeModel.audit_log_id == AuditLogModel.id)
            .where(
                AuditLogModel.tenant_id == tenant_id.value,
                EntityChangeModel.entity_type == entity_type,
                EntityChangeModel.entity_id == entity_id,
            )
            .order_by(EntityChangeModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [AuditMapper.to_entity_change_entity(model) for model in models]

    async def count_entity_changes(
        self,
        tenant_id: TenantId,
        entity_type: str,
        entity_id: str,
    ) -> int:
        """Count entity changes for a specific entity."""
        # Join with audit_logs to filter by tenant
        stmt = (
            select(func.count(EntityChangeModel.id))
            .join(AuditLogModel, EntityChangeModel.audit_log_id == AuditLogModel.id)
            .where(
                AuditLogModel.tenant_id == tenant_id.value,
                EntityChangeModel.entity_type == entity_type,
                EntityChangeModel.entity_id == entity_id,
            )
        )

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
