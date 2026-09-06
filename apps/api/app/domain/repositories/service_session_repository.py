"""
Service Session Repository Interface

Defines the contract for Service Session data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence
from datetime import datetime

from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)


class ServiceSessionRepository(BaseRepository[ServiceSessionEntity, SessionId]):
    """
    Repository interface for Service Session aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_member_id(
        self, tenant_id: TenantId, member_id: EligibleMemberId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a member within a tenant.

        Args:
            tenant_id: Tenant identifier
            member_id: Member identifier

        Returns:
            List of ServiceSessionEntity for the member
        """
        pass

    @abstractmethod
    async def get_by_provider_id(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a provider within a tenant.

        Args:
            tenant_id: Tenant identifier
            provider_id: Provider identifier

        Returns:
            List of ServiceSessionEntity for the provider
        """
        pass

    @abstractmethod
    async def get_by_service_id(
        self, tenant_id: TenantId, service_id: ServiceId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a service within a tenant.

        Args:
            tenant_id: Tenant identifier
            service_id: Service identifier

        Returns:
            List of ServiceSessionEntity for the service
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId | None = None,
        provider_id: ProviderId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "scheduled_at",
        sort_desc: bool = True,
    ) -> Sequence[ServiceSessionEntity]:
        """
        List sessions with filtering, searching, and pagination.

        Args:
            tenant_id: Tenant identifier
            member_id: Filter by member identifier
            provider_id: Filter by provider identifier
            service_id: Filter by service identifier
            status: Filter by session status
            scheduled_from: Only sessions scheduled at or after this instant
            scheduled_to: Only sessions scheduled at or before this instant
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order

        Returns:
            Sequence of ServiceSessionEntity
        """

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId | None = None,
        provider_id: ProviderId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
    ) -> int:
        """
        Count sessions matching filters.

        Must apply exactly the same filters as `list_all`.

        Args:
            tenant_id: Tenant identifier
            member_id: Filter by member identifier
            provider_id: Filter by provider identifier
            service_id: Filter by service identifier
            status: Filter by session status
            scheduled_from: Only sessions scheduled at or after this instant
            scheduled_to: Only sessions scheduled at or before this instant

        Returns:
            Total count
        """
