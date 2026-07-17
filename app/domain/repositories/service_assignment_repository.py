"""
ServiceAssignment Repository Interface

Defines the contract for ServiceAssignment data access.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId


class ServiceAssignmentRepository(BaseRepository[ServiceAssignmentEntity, ServiceAssignmentId]):
    """Repository interface for ServiceAssignment aggregate."""

    @abstractmethod
    async def get_by_service_id(
        self, service_id: ServiceId, tenant_id: TenantId
    ) -> Sequence[ServiceAssignmentEntity]:
        """Get all assignments for a service."""

    @abstractmethod
    async def get_by_contract_id(
        self, contract_id: ContractId, tenant_id: TenantId
    ) -> Sequence[ServiceAssignmentEntity]:
        """Get all assignments for a contract."""

    @abstractmethod
    async def get_by_service_and_contract(
        self, service_id: ServiceId, contract_id: ContractId, tenant_id: TenantId
    ) -> ServiceAssignmentEntity | None:
        """Get assignment by service and contract."""

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        service_id: ServiceId | None = None,
        contract_id: ContractId | None = None,
        status: BaseStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ServiceAssignmentEntity]:
        """List assignments with filtering."""

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        service_id: ServiceId | None = None,
        contract_id: ContractId | None = None,
        status: BaseStatus | None = None,
    ) -> int:
        """Count assignments matching filters."""
