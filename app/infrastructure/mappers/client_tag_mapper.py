"""ClientTag Mapper - converts between ClientTagEntity and ClientTagModel."""

from app.domain.entities.client_tag import ClientTagEntity
from app.domain.value_objects.core import ClientTagId, TenantId
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.shared.utils.datetime import ensure_utc


class ClientTagMapper:
    @staticmethod
    def to_entity(model: ClientTagModel) -> ClientTagEntity:
        return ClientTagEntity(
            _id=ClientTagId(model.id),
            _tenant_id=TenantId(model.tenant_id),
            _name=model.name,
            _description=model.description,
            _color=model.color,
            _is_active=model.is_active,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ClientTagEntity) -> ClientTagModel:
        return ClientTagModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            name=entity._name,
            description=entity._description,
            color=entity._color,
            is_active=entity._is_active,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
