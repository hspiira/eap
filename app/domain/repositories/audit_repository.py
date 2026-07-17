"""
Audit Repository Interface

Defines the contract for Audit data access.
Implementation lives in infrastructure layer.

Note: Audit logs are immutable - no update or delete operations.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.audit import AuditLog, EntityChange
from app.domain.enums import AuditActionType
from app.domain.value_objects.core import AuditLogId, TenantId, UserId


class AuditRepository:
    """
    Repository interface for Audit aggregates.

    Audit logs are immutable - only create and read operations.
    """

    @abstractmethod
    async def save_audit_log(self, audit_log: AuditLog) -> None:
        """
        Save an audit log entry.

        Args:
            audit_log: AuditLog entity to save
        """
        pass

    @abstractmethod
    async def save_entity_change(self, entity_change: EntityChange) -> None:
        """
        Save an entity change entry.

        Args:
            entity_change: EntityChange entity to save
        """
        pass

    @abstractmethod
    async def get_audit_log_by_id(
        self, audit_log_id: AuditLogId
    ) -> AuditLog | None:
        """
        Get audit log by ID.

        Args:
            audit_log_id: Audit log identifier

        Returns:
            AuditLog if found, None otherwise
        """
        pass

    @abstractmethod
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
        """
        List audit logs with filtering and pagination.
        
        Args:
            tenant_id: Tenant identifier
            user_id: Filter by user identifier
            action_type: Filter by action type
            resource_type: Filter by resource type (e.g., "Tenant", "Person")
            resource_id: Filter by resource identifier
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            
        Returns:
            Sequence of AuditLog
        """
    
    @abstractmethod
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
        """
        Count audit logs matching filters.
        
        Args:
            tenant_id: Tenant identifier
            user_id: Filter by user identifier
            action_type: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource identifier
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            
        Returns:
            Total count
        """
    
    @abstractmethod
    async def get_entity_changes_by_audit_log_id(
        self, audit_log_id: AuditLogId
    ) -> Sequence[EntityChange]:
        """
        Get all entity changes for an audit log.
        
        Args:
            audit_log_id: Audit log identifier
            
        Returns:
            Sequence of EntityChange
        """
    
    @abstractmethod
    async def get_entity_changes_by_entity(
        self,
        tenant_id: TenantId,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[EntityChange]:
        """
        Get all entity changes for a specific entity.
        
        Args:
            tenant_id: Tenant identifier
            entity_type: Entity type (e.g., "Tenant", "Person")
            entity_id: Entity identifier
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Sequence of EntityChange
        """
