"""
User Use Cases

Application services for User aggregate operations.
Refactored to use base use case classes to eliminate boilerplate.
"""

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.user import UserEntity
from app.domain.enums import TenantRole, UserStatus
from app.domain.exceptions import SubscriptionLimitError
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.utils.datetime import utc_now


# =============================================================================
# CREATE USE CASE (special - not a lifecycle operation)
# =============================================================================


class CreateUserUseCase(BaseUseCase[UserEntity, UserId]):
    """Use case for creating a new user."""

    def __init__(
        self,
        user_repository: UserRepository,
        tenant_repository: TenantRepository | None = None,
    ):
        super().__init__(user_repository)
        self.user_repository = user_repository
        self.tenant_repository = tenant_repository

    async def execute(
        self,
        user_id: UserId,
        tenant_id: TenantId,
        email: Email,
        password_hash: str | None = None,
        role: TenantRole = TenantRole.USER,
    ) -> UserEntity:
        """
        Create a new user.

        Args:
            user_id: Unique user identifier
            tenant_id: Tenant identifier
            email: User email address
            password_hash: Hashed password (optional for OAuth users)
            role: Tenant role (default USER; use ADMIN for tenant admin)

        Returns:
            Created UserEntity

        Raises:
            ValueError: If user with email already exists
            SubscriptionLimitError: If tenant user limit reached
        """
        if self.tenant_repository:
            tenant = await self.tenant_repository.get_by_id(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant not found: {tenant_id.value}")
            user_count = await self.user_repository.count(tenant_id=tenant_id)
            if not tenant.can_create_users(user_count):
                raise SubscriptionLimitError(
                    "Tenant user limit reached; upgrade subscription to add more users."
                )

        # Check if user already exists
        existing = await self.user_repository.get_by_email(email, tenant_id)
        if existing:
            raise ValueError(f"User with email {email.value} already exists")

        # Create user entity
        user = UserEntity(
            id=user_id,
            tenant_id=tenant_id,
            email=email,
            _password_hash=password_hash,
            status=UserStatus.PENDING_VERIFICATION,
            is_two_factor_enabled=False,
            role=role,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        return await self._save_and_publish_events(user)


# Lifecycle / update operations are dispatched through
# `TransitionUseCase` + `UserTransition` (see app/application/use_cases/transitions.py).


class GetUserUseCase(BaseUseCase[UserEntity, UserId]):
    """Use case for retrieving a user."""

    def __init__(self, user_repository: UserRepository):
        super().__init__(user_repository)
        self.user_repository = user_repository

    async def execute(self, user_id: UserId) -> UserEntity | None:
        """
        Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            UserEntity if found, None otherwise
        """
        return await self.repository.get_by_id(user_id)

    async def execute_by_email(
        self, email: Email, tenant_id: TenantId
    ) -> UserEntity | None:
        """
        Get user by email within a tenant.

        Args:
            email: User email
            tenant_id: Tenant identifier

        Returns:
            UserEntity if found, None otherwise
        """
        return await self.user_repository.get_by_email(email, tenant_id)
