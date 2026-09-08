"""ServiceAssignment Use Cases - Application services for ServiceAssignment operations."""

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.shared.utils.datetime import utc_now

# Lifecycle dispatched via TransitionUseCase + ServiceAssignmentTransition.


class CreateServiceAssignmentUseCase(BaseUseCase[ServiceAssignmentEntity, ServiceAssignmentId]):
    """Use case for creating a service assignment."""

    def __init__(self, assignment_repository: ServiceAssignmentRepository):
        super().__init__(assignment_repository)
        self.assignment_repository = assignment_repository

    async def execute(
        self,
        assignment_id: ServiceAssignmentId,
        tenant_id: TenantId,
        service_id: ServiceId,
        contract_id: ContractId,
        assigned_by: str | None = None,
        notes: str | None = None,
    ) -> ServiceAssignmentEntity:
        """Create a new service assignment."""
        # Check if assignment already exists
        existing = await self.assignment_repository.get_by_service_and_contract(
            service_id, contract_id, tenant_id
        )
        if existing:
            raise ValueError(
                f"Service assignment already exists for service {service_id.value} "
                f"and contract {contract_id.value}"
            )

        assignment = ServiceAssignmentEntity(
            id=assignment_id,
            tenant_id=tenant_id,
            service_id=service_id,
            contract_id=contract_id,
            status=BaseStatus.PENDING,
            assigned_by=assigned_by,
            notes=notes,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        assignment.record_created()

        return await self._save_and_publish_events(assignment)


# =============================================================================
# UPDATE USE CASE
# =============================================================================


class UpdateServiceAssignmentUseCase(BaseUseCase[ServiceAssignmentEntity, ServiceAssignmentId]):
    """Use case for updating a service assignment."""

    def __init__(self, assignment_repository: ServiceAssignmentRepository):
        super().__init__(assignment_repository)

    async def execute(
        self, assignment_id: ServiceAssignmentId, notes: str | None
    ) -> ServiceAssignmentEntity:
        """Update a service assignment."""
        assignment = await self._get_entity_or_raise(assignment_id, "Assignment")
        assignment.update_notes(notes)
        return await self._save_and_publish_events(assignment)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetServiceAssignmentUseCase(BaseUseCase[ServiceAssignmentEntity, ServiceAssignmentId]):
    """Use case for retrieving a service assignment."""

    def __init__(self, assignment_repository: ServiceAssignmentRepository):
        super().__init__(assignment_repository)

    async def execute(self, assignment_id: ServiceAssignmentId) -> ServiceAssignmentEntity | None:
        """Get service assignment by ID."""
        return await self.repository.get_by_id(assignment_id)
