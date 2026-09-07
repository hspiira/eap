"""Mapper for practitioner engagement-document checklist entries."""

from app.domain.entities.provider_engagement_document import ProviderEngagementDocument
from app.domain.value_objects.ids import ProviderEngagementDocumentId, ProviderId, TenantId
from app.infrastructure.models.provider_engagement_document_model import (
    ProviderEngagementDocumentModel,
)
from app.shared.utils.datetime import ensure_utc


class ProviderEngagementDocumentMapper:
    @staticmethod
    def to_entity(model: ProviderEngagementDocumentModel) -> ProviderEngagementDocument:
        return ProviderEngagementDocument(
            id=ProviderEngagementDocumentId(model.id),
            tenant_id=TenantId(model.tenant_id),
            provider_id=ProviderId(model.provider_id),
            document_kind=model.document_kind,
            state=model.state,
            note=model.note,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: ProviderEngagementDocument) -> ProviderEngagementDocumentModel:
        return ProviderEngagementDocumentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            provider_id=entity.provider_id.value,
            document_kind=entity.document_kind,
            state=entity.state,
            note=entity.note,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
