"""
Tenant Mapper

Converts between TenantEntity (domain) and TenantModel (persistence).
"""

from app.domain.entities.tenant import TenantEntity
from app.domain.value_objects.core import TenantId, TenantCode, TenantSettings
from app.domain.enums import TenantStatus, SubscriptionTier
from app.infrastructure.models.tenant_model import TenantModel
from app.shared.utils.datetime import ensure_utc


class TenantMapper:
    """Mapper for TenantEntity ↔ TenantModel conversion"""
    
    @staticmethod
    def to_entity(model: TenantModel) -> TenantEntity:
        """
        Convert database model to domain entity.
        
        Args:
            model: TenantModel from database
            
        Returns:
            TenantEntity with business logic
        """
        # Reconstruct value objects
        tenant_id = TenantId(model.id)
        tenant_code = TenantCode(model.code)
        
        # Reconstruct TenantSettings from JSON
        settings_dict = model.settings if isinstance(model.settings, dict) else {}
        tenant_settings = TenantSettings(
            max_users=settings_dict.get("max_users", 0),
            max_clients=settings_dict.get("max_clients", 0),
            features_enabled=tuple(settings_dict.get("features_enabled", [])),
            custom_branding=settings_dict.get("custom_branding", False)
        )
        
        # Reconstruct enums
        status = TenantStatus(model.status)
        subscription_tier = SubscriptionTier(model.subscription_tier)
        
        # Create entity
        return TenantEntity(
            _id=tenant_id,
            _name=model.name,
            _code=tenant_code,
            _status=status,
            _settings=tenant_settings,
            _subscription_tier=subscription_tier,
            _deleted_at=ensure_utc(model.deleted_at),
            _updated_at=ensure_utc(model.updated_at)
        )
    
    @staticmethod
    def to_model(entity: TenantEntity) -> TenantModel:
        """
        Convert domain entity to database model.
        
        Args:
            entity: TenantEntity with business logic
            
        Returns:
            TenantModel for persistence
        """
        # Convert value objects to primitives
        settings_dict = {
            "max_users": entity._settings.max_users,
            "max_clients": entity._settings.max_clients,
            "features_enabled": list(entity._settings.features_enabled),
            "custom_branding": entity._settings.custom_branding
        }
        
        # Create model
        # Note: created_at and updated_at are handled by TimestampMixin
        # but we can set updated_at explicitly if needed
        model = TenantModel(
            id=entity._id.value,
            name=entity._name,
            code=entity._code.value,
            status=entity._status.value,
            settings=settings_dict,
            subscription_tier=entity._subscription_tier.value,
            deleted_at=entity._deleted_at
        )
        
        # Set updated_at if provided (otherwise TimestampMixin will handle it)
        if entity._updated_at:
            model.updated_at = entity._updated_at
        
        return model
