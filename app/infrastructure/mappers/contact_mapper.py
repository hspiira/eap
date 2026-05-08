"""Contact Mapper - converts between ContactEntity and ContactModel."""

from app.domain.entities.contact import ContactEntity
from app.domain.value_objects.core import ContactId, Email, TenantId
from app.infrastructure.models.contact_model import ContactModel
from app.shared.utils.datetime import ensure_utc


class ContactMapper:
    @staticmethod
    def to_entity(model: ContactModel) -> ContactEntity:
        return ContactEntity(
            id=ContactId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=model.client_id,
            name=model.name,
            title=model.title,
            email=Email(model.email) if model.email else None,
            phone=model.phone,
            department=model.department,
            is_primary=model.is_primary,
            notes=model.notes,
            _is_active=model.is_active,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ContactEntity) -> ContactModel:
        return ContactModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id,
            name=entity.name,
            title=entity.title,
            email=entity.email.value if entity.email else None,
            phone=entity.phone,
            department=entity.department,
            is_primary=entity.is_primary,
            notes=entity.notes,
            is_active=entity._is_active,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
