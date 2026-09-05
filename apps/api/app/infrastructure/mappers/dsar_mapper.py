"""DSAR request mapper (Phase 4 #DSAR)."""

from app.domain.entities.dsar_request import DSARRequest
from app.domain.enums import DSARRequestStatus, DSARRequestType
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
    UserId,
)
from app.infrastructure.models.dsar_model import DSARRequestModel
from app.shared.utils.datetime import ensure_utc


class DSARRequestMapper:
    @staticmethod
    def to_entity(model: DSARRequestModel) -> DSARRequest:
        entity = DSARRequest(
            id=DSARRequestId(model.id),
            tenant_id=TenantId(model.tenant_id),
            subject_person_id=PersonId(model.subject_person_id),
            request_type=DSARRequestType(model.request_type),
            status=DSARRequestStatus(model.status),
            requested_by=UserId(model.requested_by),
            started_at=ensure_utc(model.started_at) if model.started_at else None,
            completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            failed_reason=model.failed_reason,
            output=model.output,
            erasure_executes_at=ensure_utc(model.erasure_executes_at)
            if model.erasure_executes_at
            else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: DSARRequest) -> DSARRequestModel:
        return DSARRequestModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            subject_person_id=entity.subject_person_id.value,
            request_type=entity.request_type,
            status=entity.status,
            requested_by=entity.requested_by.value,
            started_at=ensure_utc(entity.started_at) if entity.started_at else None,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            failed_reason=entity.failed_reason,
            output=entity.output,
            erasure_executes_at=ensure_utc(entity.erasure_executes_at)
            if entity.erasure_executes_at
            else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
