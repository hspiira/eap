"""Non-compete clause mapper (Phase 2 #D-Provider)."""

from app.domain.entities.non_compete_clause import NonCompeteClauseEntity
from app.domain.enums import NonCompeteStatus
from app.domain.value_objects.core import (
    NonCompeteClauseId,
    ProviderId,
    TenantId,
    UserId,
)
from app.infrastructure.models.non_compete_clause_model import (
    NonCompeteClauseModel,
)
from app.shared.utils.datetime import ensure_utc


class NonCompeteClauseMapper:
    @staticmethod
    def to_entity(model: NonCompeteClauseModel) -> NonCompeteClauseEntity:
        entity = NonCompeteClauseEntity(
            id=NonCompeteClauseId(model.id),
            tenant_id=TenantId(model.tenant_id),
            provider_id=ProviderId(model.provider_id),
            status=NonCompeteStatus(model.status),
            terms_summary=model.terms_summary,
            effective_from=model.effective_from,
            effective_until=model.effective_until,
            signed_at=ensure_utc(model.signed_at) if model.signed_at else None,
            signed_by=UserId(model.signed_by) if model.signed_by else None,
            revoked_at=ensure_utc(model.revoked_at) if model.revoked_at else None,
            revoked_reason=model.revoked_reason,
            document_id=model.document_id,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: NonCompeteClauseEntity) -> NonCompeteClauseModel:
        return NonCompeteClauseModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            provider_id=entity.provider_id.value,
            status=entity.status,
            terms_summary=entity.terms_summary,
            effective_from=entity.effective_from,
            effective_until=entity.effective_until,
            signed_at=ensure_utc(entity.signed_at) if entity.signed_at else None,
            signed_by=entity.signed_by.value if entity.signed_by else None,
            revoked_at=ensure_utc(entity.revoked_at) if entity.revoked_at else None,
            revoked_reason=entity.revoked_reason,
            document_id=entity.document_id,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
