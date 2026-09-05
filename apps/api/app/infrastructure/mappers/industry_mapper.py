"""Industry Mapper - converts between IndustryEntity and IndustryModel."""

from app.domain.entities.industry import IndustryEntity
from app.domain.value_objects.core import IndustryId, TenantId
from app.infrastructure.models.industry_model import IndustryModel
from app.shared.utils.datetime import ensure_utc


class IndustryMapper:
    @staticmethod
    def to_entity(model: IndustryModel) -> IndustryEntity:
        return IndustryEntity(
            id=IndustryId(model.id),
            tenant_id=TenantId(model.tenant_id),
            name=model.name,
            description=model.description,
            parent_industry_id=IndustryId(model.parent_industry_id)
            if model.parent_industry_id
            else None,
            code=model.code,
            _is_active=model.is_active,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: IndustryEntity) -> IndustryModel:
        return IndustryModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            name=entity.name,
            description=entity.description,
            parent_industry_id=entity.parent_industry_id.value
            if entity.parent_industry_id
            else None,
            code=entity.code,
            is_active=entity._is_active,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
