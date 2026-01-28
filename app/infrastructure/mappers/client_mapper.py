"""
Client Mapper

Converts between ClientEntity (domain) and ClientModel (persistence).
"""

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ContactMethod
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    Email,
    IndustryId,
    TenantId,
)
from app.infrastructure.models.client_model import ClientModel
from app.shared.utils.datetime import ensure_utc


class ClientMapper:
    """Mapper for ClientEntity ↔ ClientModel conversion"""

    @staticmethod
    def to_entity(model: ClientModel) -> ClientEntity:
        """
        Convert database model to domain entity.

        Args:
            model: ClientModel from database

        Returns:
            ClientEntity with business logic
        """
        # Reconstruct value objects
        client_id = ClientId(model.id)
        tenant_id = TenantId(model.tenant_id)

        # Reconstruct ContactInfo from JSON
        contact_dict = model.contact_info if isinstance(model.contact_info, dict) else {}
        email_value = contact_dict.get("email")
        contact_info = ContactInfo(
            phone=contact_dict.get("phone"),
            email=Email(email_value) if email_value else None,
            address=contact_dict.get("address"),
        )

        # Reconstruct Address from JSON (if present)
        billing_address = None
        if model.billing_address and isinstance(model.billing_address, dict):
            addr_dict = model.billing_address
            billing_address = Address(
                street=addr_dict["street"],
                city=addr_dict["city"],
                country=addr_dict["country"],
                postal_code=addr_dict.get("postal_code"),
            )

        # Reconstruct optional value objects
        industry_id = IndustryId(model.industry_id) if model.industry_id else None
        parent_client_id = (
            ClientId(model.parent_client_id) if model.parent_client_id else None
        )

        # Reconstruct enums
        status = BaseStatus(model.status)
        preferred_contact_method = (
            ContactMethod(model.preferred_contact_method)
            if model.preferred_contact_method
            else None
        )

        # Create entity
        return ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name=model.name,
            _code=model.code,
            _contact_info=contact_info,
            _billing_address=billing_address,
            _industry_id=industry_id,
            _parent_client_id=parent_client_id,
            _status=status,
            _is_verified=model.is_verified,
            _preferred_contact_method=preferred_contact_method,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ClientEntity) -> ClientModel:
        """
        Convert domain entity to database model.

        Args:
            entity: ClientEntity with business logic

        Returns:
            TenantModel for persistence
        """
        # Serialize ContactInfo to JSON
        contact_dict = {
            "phone": entity._contact_info.phone,
            "email": entity._contact_info.email.value if entity._contact_info.email else None,
            "address": entity._contact_info.address,
        }

        # Serialize Address to JSON (if present)
        billing_address_dict = None
        if entity._billing_address:
            billing_address_dict = {
                "street": entity._billing_address.street,
                "city": entity._billing_address.city,
                "country": entity._billing_address.country,
                "postal_code": entity._billing_address.postal_code,
            }

        # Create model
        return ClientModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            name=entity._name,
            code=entity._code,
            contact_info=contact_dict,
            billing_address=billing_address_dict,
            industry_id=entity._industry_id.value if entity._industry_id else None,
            parent_client_id=entity._parent_client_id.value
            if entity._parent_client_id
            else None,
            status=entity._status,
            is_verified=entity._is_verified,
            preferred_contact_method=entity._preferred_contact_method,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
