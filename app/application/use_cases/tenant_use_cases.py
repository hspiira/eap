"""
Tenant Use Cases

Application services for Tenant aggregate operations.
Refactored to use base use case classes.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from app.application.use_cases.base import (
    BaseUseCase,
    create_activate_use_case,
    create_archive_use_case,
    create_restore_use_case,
    create_suspend_use_case,
    create_terminate_use_case,
)
from app.application.use_cases.user_use_cases import CreateUserUseCase, ActivateUserUseCase, VerifyUserEmailUseCase
from app.core.security import hash_password
from app.domain.entities.tenant import TenantEntity
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantCode, TenantId, TenantSettings, UserId
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.password_generator import generate_secure_password

if TYPE_CHECKING:
    from app.infrastructure.repositories.password_set_token_repository import (
        PasswordSetTokenRepository,
    )


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

    def __init__(
        self,
        tenant_repository: TenantRepository,
        user_repository: UserRepository | None = None,
        industry_repository: IndustryRepository | None = None,
        password_set_token_repository: "PasswordSetTokenRepository | None" = None,
    ):
        super().__init__(tenant_repository)
        self.tenant_repository = tenant_repository
        self.user_repository = user_repository
        self.industry_repository = industry_repository
        self.password_set_token_repository = password_set_token_repository

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
    ) -> tuple[
        TenantEntity,
        str,
        str | None,
        str | None,
        datetime | None,
    ]:
        """
        Create a new tenant and an admin user.

        When password_set_token_repository is provided, admin is created with
        an unusable placeholder password and a set-password token is issued;
        the caller should redirect the user to set_password_url to set a
        password and then log in. Otherwise a random admin password is
        generated and returned (legacy behaviour).

        Returns:
            Tuple of (TenantEntity, admin_email, admin_password, set_password_token, set_password_expires_at).
            admin_password is None when set_password_token is set; set_password_* are None otherwise.
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

        tenant = await self._save_and_publish_events(tenant)

        # Seed default industries for the tenant
        if self.industry_repository:
            from app.application.services.industry_seeder import seed_industries_for_tenant
            await seed_industries_for_tenant(tenant.id, self.industry_repository)

        # Create admin user if user_repository is provided
        admin_email = f"admin_{tenant.code.value}@evexia.test"
        admin_password: str | None = None
        set_password_token: str | None = None
        set_password_expires_at: datetime | None = None

        if self.user_repository:
            (
                admin_password,
                set_password_token,
                set_password_expires_at,
            ) = await self._create_admin_user(tenant)

        return (
            tenant,
            admin_email,
            admin_password,
            set_password_token,
            set_password_expires_at,
        )

    async def _create_admin_user(
        self, tenant: TenantEntity
    ) -> tuple[str | None, str | None, datetime | None]:
        """
        Create an admin user for the tenant.

        When password_set_token_repository is set, uses a placeholder
        password and creates a set-password token. Otherwise generates
        a secure password and returns it.

        Returns:
            (admin_password, set_password_token, set_password_expires_at).
            Either admin_password is set or (set_password_token, set_password_expires_at) are set.
        """
        from app.domain.enums import TenantRole

        use_set_password_flow = self.password_set_token_repository is not None
        admin_password: str | None = None

        if use_set_password_flow:
            # Placeholder hash so user cannot log in until they set password
            placeholder = hash_password(
                generate_secure_password(length=32)  # never exposed
            )
            password_hash = placeholder
        else:
            admin_password = generate_secure_password(length=16)
            password_hash = hash_password(admin_password)

        admin_email = Email(f"admin_{tenant.code.value}@evexia.test")
        user_id = UserId(generate_cuid())

        create_user_use_case = CreateUserUseCase(self.user_repository)
        admin_user = await create_user_use_case.execute(
            user_id=user_id,
            tenant_id=tenant.id,
            email=admin_email,
            password_hash=password_hash,
            role=TenantRole.ADMIN,
        )

        activate_use_case = ActivateUserUseCase(self.user_repository)
        await activate_use_case.execute(admin_user.id)

        verify_email_use_case = VerifyUserEmailUseCase(self.user_repository)
        await verify_email_use_case.execute(admin_user.id)

        set_password_token_val: str | None = None
        set_password_expires_at_val: datetime | None = None

        if use_set_password_flow and self.password_set_token_repository:
            set_password_token_val, set_password_expires_at_val = (
                await self.password_set_token_repository.create(admin_user.id.value)
            )

        return (
            admin_password,
            set_password_token_val,
            set_password_expires_at_val,
        )


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
