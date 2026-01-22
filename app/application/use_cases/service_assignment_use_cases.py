"""ServiceAssignment Use Cases - Application services for ServiceAssignment operations."""

from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.shared.utils.datetime import utc_now


class CreateServiceAssignmentUseCase:
    def __init__(self, assignment_repository: ServiceAssignmentRepository):
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
        # Check if assignment already exists
        existing = await self.assignment_repository.get_by_service_and_contract(
            service_id, contract_id, tenant_id
        )
        if existing:
            raise ValueError(f"Service assignment already exists for service {service_id.value} and contract {contract_id.value}")

        assignment = ServiceAssignmentEntity(
            _id=assignment_id,
            _tenant_id=tenant_id,
            _service_id=service_id,
            _contract_id=contract_id,
            _status=BaseStatus.PENDING,
            _assigned_by=assigned_by,
            _notes=notes,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        await self.assignment_repository.save(assignment)
        return assignment


class ActivateServiceAssignmentUseCase:
    def __init__(self, assignment_repository: ServiceAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(self, assignment_id: ServiceAssignmentId) -> ServiceAssignmentEntity:
        assignment = await self.assignment_repository.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id.value} not found")
        assignment.activate()
        await self.assignment_repository.save(assignment)
        return assignment


class DeactivateServiceAssignmentUseCase:
    def __init__(self, assignment_repository: ServiceAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(self, assignment_id: ServiceAssignmentId) -> ServiceAssignmentEntity:
        assignment = await self.assignment_repository.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id.value} not found")
        assignment.deactivate()
        await self.assignment_repository.save(assignment)
        return assignment


class UpdateServiceAssignmentUseCase:
    def __init__(self, assignment_repository: ServiceAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(
        self, assignment_id: ServiceAssignmentId, notes: str | None
    ) -> ServiceAssignmentEntity:
        assignment = await self.assignment_repository.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id.value} not found")
        assignment.update_notes(notes)
        await self.assignment_repository.save(assignment)
        return assignment


class GetServiceAssignmentUseCase:
    def __init__(self, assignment_repository: ServiceAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(self, assignment_id: ServiceAssignmentId) -> ServiceAssignmentEntity | None:
        return await self.assignment_repository.get_by_id(assignment_id)
