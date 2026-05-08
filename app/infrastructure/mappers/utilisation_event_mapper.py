"""Utilisation event mapper (Phase 2 #D-Pricing)."""

from app.domain.entities.utilisation_event import UtilisationEventEntity
from app.domain.enums import UtilisationEventType
from app.domain.value_objects.core import (
    ContractId,
    TenantId,
    UtilisationEventId,
)
from app.infrastructure.models.utilisation_event_model import (
    UtilisationEventModel,
)
from app.shared.utils.datetime import ensure_utc


class UtilisationEventMapper:
    @staticmethod
    def to_entity(model: UtilisationEventModel) -> UtilisationEventEntity:
        return UtilisationEventEntity(
            id=UtilisationEventId(model.id),
            tenant_id=TenantId(model.tenant_id),
            contract_id=ContractId(model.contract_id),
            event_type=UtilisationEventType(model.event_type),
            occurred_on=model.occurred_on,
            units=model.units,
            service_code=model.service_code,
            source_id=model.source_id,
            notes=model.notes,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: UtilisationEventEntity) -> UtilisationEventModel:
        return UtilisationEventModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            contract_id=entity.contract_id.value,
            event_type=entity.event_type,
            occurred_on=entity.occurred_on,
            units=entity.units,
            service_code=entity.service_code,
            source_id=entity.source_id,
            notes=entity.notes,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
