"""Industry Mapper - converts between IndustryEntity and IndustryModel."""

from app.domain.entities.industry import IndustryEntity
from app.domain.value_objects.core import IndustryId, TenantId
from app.infrastructure.models.industry_model import IndustryModel
from app.shared.utils.datetime import ensure_utc


class IndustryMapper:
    @staticmethod
    def to_entity(model: IndustryModel) -> IndustryEntity:
        return IndustryEntity(
            _id=IndustryId(model.id),
            _tenant_id=TenantId(model.tenant_id),
            _name=model.name,
            _description=model.description,
            _parent_industry_id=IndustryId(model.parent_industry_id) if model.parent_industry_id else None,
            _code=model.code,
            _is_active=model.is_active,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: IndustryEntity) -> IndustryModel:
        return IndustryModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            name=entity._name,
            description=entity._description,
            parent_industry_id=entity._parent_industry_id.value if entity._parent_industry_id else None,
            code=entity._code,
            is_active=entity._is_active,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
