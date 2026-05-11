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
            id=tenant_id,
            name=model.name,
            code=tenant_code,
            status=status,
            settings=tenant_settings,
            subscription_tier=subscription_tier,
            deleted_at=ensure_utc(model.deleted_at),
            updated_at=ensure_utc(model.updated_at),
            azure_tenant_id=model.azure_tenant_id,
            azure_sso_enabled=model.azure_sso_enabled,
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
            "max_users": entity.settings.max_users,
            "max_clients": entity.settings.max_clients,
            "features_enabled": list(entity.settings.features_enabled),
            "custom_branding": entity.settings.custom_branding
        }
        
        # Create model
        # Note: created_at and updated_at are handled by TimestampMixin
        # but we can set updated_at explicitly if needed
        # For SQLEnum with native_enum=False, we need to ensure enum values are used
        model = TenantModel(
            id=entity.id.value,
            name=entity.name,
            code=entity.code.value,
            status=entity.status,
            settings=settings_dict,
            subscription_tier=entity.subscription_tier,
            deleted_at=entity.deleted_at,
            azure_tenant_id=entity.azure_tenant_id,
            azure_sso_enabled=entity.azure_sso_enabled,
        )
        
        # Set updated_at if provided (otherwise TimestampMixin will handle it)
        if entity.updated_at:
            model.updated_at = entity.updated_at
        
        return model
