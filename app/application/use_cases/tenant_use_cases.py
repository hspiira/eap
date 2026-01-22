"""
Tenant Use Cases

Application services for Tenant aggregate operations.
Commands only - queries use repositories directly.
"""

from app.domain.entities.tenant import TenantEntity
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantCode, TenantId, TenantSettings
from app.shared.utils.datetime import utc_now


class CreateTenantUseCase:
    """Use case for creating a new tenant."""

    def __init__(self, tenant_repository: TenantRepository):
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
        """
        Create a new tenant.

        Args:
            tenant_id: Unique tenant identifier
            name: Tenant name
            code: Tenant code (3-15 chars, lowercase alphanumeric)
            subscription_tier: Subscription tier
            max_users: Maximum users allowed
            max_clients: Maximum clients allowed
            features_enabled: Enabled features
            custom_branding: Whether custom branding is enabled

        Returns:
            Created TenantEntity

        Raises:
            ValueError: If tenant with code already exists
        """
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

        # Save tenant
        await self.tenant_repository.save(tenant)

        return tenant


class ActivateTenantUseCase:
    """Use case for activating a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def execute(self, tenant_id: TenantId) -> TenantEntity:
        """
        Activate a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Activated TenantEntity

        Raises:
            ValueError: If tenant not found
            DomainError: If tenant cannot be activated
        """
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id.value} not found")

        tenant.activate()
        await self.tenant_repository.save(tenant)

        return tenant


class SuspendTenantUseCase:
    """Use case for suspending a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def execute(self, tenant_id: TenantId, reason: str) -> TenantEntity:
        """
        Suspend a tenant.

        Args:
            tenant_id: Tenant identifier
            reason: Suspension reason

        Returns:
            Suspended TenantEntity

        Raises:
            ValueError: If tenant not found
            DomainError: If suspension is invalid
        """
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id.value} not found")

        tenant.suspend(reason)
        await self.tenant_repository.save(tenant)

        return tenant


class TerminateTenantUseCase:
    """Use case for terminating a tenant."""

    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def execute(self, tenant_id: TenantId, reason: str) -> TenantEntity:
        """
        Terminate a tenant.

        Args:
            tenant_id: Tenant identifier
            reason: Termination reason

        Returns:
            Terminated TenantEntity

        Raises:
            ValueError: If tenant not found
            DomainError: If termination is invalid
        """
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id.value} not found")

        tenant.terminate(reason)
        await self.tenant_repository.save(tenant)

        return tenant


class UpdateTenantSettingsUseCase:
    """Use case for updating tenant settings."""

    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def execute(
        self,
        tenant_id: TenantId,
        max_users: int | None = None,
        max_clients: int | None = None,
        features_enabled: tuple[str, ...] | None = None,
        custom_branding: bool | None = None,
    ) -> TenantEntity:
        """
        Update tenant settings.

        Args:
            tenant_id: Tenant identifier
            max_users: Maximum users (optional)
            max_clients: Maximum clients (optional)
            features_enabled: Enabled features (optional)
            custom_branding: Custom branding flag (optional)

        Returns:
            Updated TenantEntity

        Raises:
            ValueError: If tenant not found
        """
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id.value} not found")

        # Create new settings with updated values
        new_settings = TenantSettings(
            max_users=max_users if max_users is not None else tenant._settings.max_users,
            max_clients=max_clients if max_clients is not None else tenant._settings.max_clients,
            features_enabled=features_enabled if features_enabled is not None else tenant._settings.features_enabled,
            custom_branding=custom_branding if custom_branding is not None else tenant._settings.custom_branding,
        )

        tenant.update_settings(new_settings)
        await self.tenant_repository.save(tenant)

        return tenant
