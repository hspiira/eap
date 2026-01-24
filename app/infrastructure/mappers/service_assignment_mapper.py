"""ServiceAssignment Mapper - converts between ServiceAssignmentEntity and ServiceAssignmentModel."""

from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.shared.utils.datetime import ensure_utc


class ServiceAssignmentMapper:
    @staticmethod
    def to_entity(model: ServiceAssignmentModel) -> ServiceAssignmentEntity:
        return ServiceAssignmentEntity(
            _id=ServiceAssignmentId(model.id),
            _tenant_id=TenantId(model.tenant_id),
            _service_id=ServiceId(model.service_id),
            _contract_id=ContractId(model.contract_id),
            _status=model.status,
            _assigned_at=ensure_utc(model.assigned_at) if model.assigned_at else None,
            _assigned_by=model.assigned_by,
            _notes=model.notes,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ServiceAssignmentEntity) -> ServiceAssignmentModel:
        return ServiceAssignmentModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            service_id=entity._service_id.value,
            contract_id=entity._contract_id.value,
            status=entity._status,
            assigned_at=ensure_utc(entity._assigned_at) if entity._assigned_at else None,
            assigned_by=entity._assigned_by,
            notes=entity._notes,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
