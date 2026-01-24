"""Contact Mapper - converts between ContactEntity and ContactModel."""

from app.domain.entities.contact import ContactEntity
from app.domain.value_objects.core import ContactId, Email, TenantId
from app.infrastructure.models.contact_model import ContactModel
from app.shared.utils.datetime import ensure_utc


class ContactMapper:
    @staticmethod
    def to_entity(model: ContactModel) -> ContactEntity:
        return ContactEntity(
            _id=ContactId(model.id),
            _tenant_id=TenantId(model.tenant_id),
            _client_id=model.client_id,
            _name=model.name,
            _title=model.title,
            _email=Email(model.email) if model.email else None,
            _phone=model.phone,
            _department=model.department,
            _is_primary=model.is_primary,
            _notes=model.notes,
            _is_active=model.is_active,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ContactEntity) -> ContactModel:
        return ContactModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            client_id=entity._client_id,
            name=entity._name,
            title=entity._title,
            email=entity._email.value if entity._email else None,
            phone=entity._phone,
            department=entity._department,
            is_primary=entity._is_primary,
            notes=entity._notes,
            is_active=entity._is_active,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
