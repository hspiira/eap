"""
Tenant Use Cases

Application services for Tenant aggregate operations.
Refactored to use base use case classes.
"""

from app.application.use_cases.base import (
    BaseUseCase,
    create_activate_use_case,
    create_archive_use_case,
    create_restore_use_case,
    create_suspend_use_case,
    create_terminate_use_case,
)
from app.domain.entities.tenant import TenantEntity
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantCode, TenantId, TenantSettings
from app.shared.utils.datetime import utc_now


# =============================================================================
# LIFECYCLE USE CASES (Using Base Factories)
# =============================================================================


class ActivateTenantUseCase:
    """Use case for activating a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self._use_case = create_activate_use_case(tenant_repository, "Tenant")

    async def execute(self, tenant_id: TenantId) -> TenantEntity:
        return await self._use_case.execute(tenant_id)


class SuspendTenantUseCase:
    """Use case for suspending a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self._use_case = create_suspend_use_case(tenant_repository, "Tenant")

    async def execute(self, tenant_id: TenantId, reason: str) -> TenantEntity:
        return await self._use_case.execute(tenant_id, reason=reason)


class TerminateTenantUseCase:
    """Use case for terminating a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self._use_case = create_terminate_use_case(tenant_repository, "Tenant")

    async def execute(self, tenant_id: TenantId, reason: str) -> TenantEntity:
        return await self._use_case.execute(tenant_id, reason=reason)


class ArchiveTenantUseCase:
    """Use case for archiving a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self._use_case = create_archive_use_case(tenant_repository, "Tenant")

    async def execute(self, tenant_id: TenantId) -> TenantEntity:
        return await self._use_case.execute(tenant_id)


class RestoreTenantUseCase:
    """Use case for restoring a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self._use_case = create_restore_use_case(tenant_repository, "Tenant")

    async def execute(self, tenant_id: TenantId) -> TenantEntity:
        return await self._use_case.execute(tenant_id)


# =============================================================================
# CREATE USE CASE
# =============================================================================


class CreateTenantUseCase(BaseUseCase[TenantEntity, TenantId]):
    """Use case for creating a new tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        super().__init__(tenant_repository)
        self.tenant_repository = tenant_repository

    async def execute(
        self,
        tenant_id: TenantId,
        name: str,
        code: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        max_users: int = 10,
        max_clients: int = 5,
        features_enabled: tuple[str, ...] = (),
        custom_branding: bool = False,
    ) -> TenantEntity:
        """Create a new tenant."""
        # Check if tenant already exists
        existing = await self.tenant_repository.get_by_code(code)
        if existing:
            raise ValueError(f"Tenant with code '{code}' already exists")

        # Create value objects
        tenant_code = TenantCode(code)
        tenant_settings = TenantSettings(
            max_users=max_users,
            max_clients=max_clients,
            features_enabled=features_enabled,
            custom_branding=custom_branding,
        )

        # Create tenant entity
        tenant = TenantEntity(
            _id=tenant_id,
            _name=name,
            _code=tenant_code,
            _status=TenantStatus.ACTIVE,
            _settings=tenant_settings,
            _subscription_tier=subscription_tier,
            _deleted_at=None,
            _updated_at=utc_now(),
        )

        return await self._save_and_publish_events(tenant)


# =============================================================================
# UPDATE USE CASES
# =============================================================================


class UpdateTenantSettingsUseCase(BaseUseCase[TenantEntity, TenantId]):
    """Use case for updating tenant settings."""

    def __init__(self, tenant_repository: TenantRepository):
        super().__init__(tenant_repository)

    async def execute(
        self,
        tenant_id: TenantId,
        max_users: int | None = None,
        max_clients: int | None = None,
        features_enabled: tuple[str, ...] | None = None,
        custom_branding: bool | None = None,
    ) -> TenantEntity:
        """Update tenant settings."""
        tenant = await self._get_entity_or_raise(tenant_id, "Tenant")

        # Create new settings with updated values
        new_settings = TenantSettings(
            max_users=max_users if max_users is not None else tenant.settings.max_users,
            max_clients=max_clients if max_clients is not None else tenant.settings.max_clients,
            features_enabled=features_enabled if features_enabled is not None else tenant.settings.features_enabled,
            custom_branding=custom_branding if custom_branding is not None else tenant.settings.custom_branding,
        )

        tenant.update_settings(new_settings)
        return await self._save_and_publish_events(tenant)


class UpdateTenantUseCase(BaseUseCase[TenantEntity, TenantId]):
    """Use case for updating tenant basic information."""

    def __init__(self, tenant_repository: TenantRepository):
        super().__init__(tenant_repository)

    async def execute(
        self,
        tenant_id: TenantId,
        name: str | None = None,
    ) -> TenantEntity:
        """Update tenant basic information."""
        tenant = await self._get_entity_or_raise(tenant_id, "Tenant")

        if name is not None:
            tenant.update_name(name)

        return await self._save_and_publish_events(tenant)


class UpdateSubscriptionUseCase(BaseUseCase[TenantEntity, TenantId]):
    """Use case for updating tenant subscription tier."""

    def __init__(self, tenant_repository: TenantRepository):
        super().__init__(tenant_repository)

    async def execute(
        self,
        tenant_id: TenantId,
        subscription_tier: SubscriptionTier,
    ) -> TenantEntity:
        """Update tenant subscription tier."""
        tenant = await self._get_entity_or_raise(tenant_id, "Tenant")
        tenant.update_subscription_tier(subscription_tier)
        return await self._save_and_publish_events(tenant)
