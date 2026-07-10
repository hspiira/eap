"""ClientTag Mapper - converts between ClientTagEntity and ClientTagModel."""

from app.domain.entities.client_tag import ClientTagEntity
from app.domain.value_objects.core import ClientTagId, TenantId
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.shared.utils.datetime import ensure_utc


class ClientTagMapper:
    @staticmethod
    def to_entity(model: ClientTagModel) -> ClientTagEntity:
        return ClientTagEntity(
            id=ClientTagId(model.id),
            tenant_id=TenantId(model.tenant_id),
            name=model.name,
            description=model.description,
            color=model.color,
            _is_active=model.is_active,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ClientTagEntity) -> ClientTagModel:
        return ClientTagModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            name=entity.name,
            description=entity.description,
            color=entity.color,
            is_active=entity._is_active,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
