"""ServiceAssignment Mapper - converts between ServiceAssignmentEntity and ServiceAssignmentModel."""

from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.shared.utils.datetime import ensure_utc


class ServiceAssignmentMapper:
    @staticmethod
    def to_entity(model: ServiceAssignmentModel) -> ServiceAssignmentEntity:
        return ServiceAssignmentEntity(
            id=ServiceAssignmentId(model.id),
            tenant_id=TenantId(model.tenant_id),
            service_id=ServiceId(model.service_id),
            contract_id=ContractId(model.contract_id),
            status=model.status,
            assigned_at=ensure_utc(model.assigned_at) if model.assigned_at else None,
            assigned_by=model.assigned_by,
            notes=model.notes,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ServiceAssignmentEntity) -> ServiceAssignmentModel:
        return ServiceAssignmentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            service_id=entity.service_id.value,
            contract_id=entity.contract_id.value,
            status=entity.status,
            assigned_at=ensure_utc(entity.assigned_at) if entity.assigned_at else None,
            assigned_by=entity.assigned_by,
            notes=entity.notes,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
