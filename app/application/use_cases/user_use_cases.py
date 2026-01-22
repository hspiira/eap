"""
User Use Cases

Application services for User aggregate operations.
"""

from app.domain.entities.user import UserEntity
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.utils.datetime import utc_now


class CreateUserUseCase:
    """Use case for creating a new user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        user_id: UserId,
        tenant_id: TenantId,
        email: Email,
        password_hash: str | None = None,
    ) -> UserEntity:
        """
        Create a new user.

        Args:
            user_id: Unique user identifier
            tenant_id: Tenant identifier
            email: User email address
            password_hash: Hashed password (optional for OAuth users)

        Returns:
            Created UserEntity

        Raises:
            ValueError: If user with email already exists
        """
        # Check if user already exists
        existing = await self.user_repository.get_by_email(email.value, tenant_id)
        if existing:
            raise ValueError(f"User with email {email.value} already exists")

        from app.domain.enums import UserStatus

        # Create user entity
        user = UserEntity(
            _id=user_id,
            _tenant_id=tenant_id,
            _email=email,
            _password_hash=password_hash,
            _status=UserStatus.PENDING_VERIFICATION,
            _is_two_factor_enabled=False,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        # Save user
        await self.user_repository.save(user)

        return user


class ActivateUserUseCase:
    """Use case for activating a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId) -> UserEntity:
        """
        Activate a user.

        Args:
            user_id: User identifier

        Returns:
            Activated UserEntity

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.activate()
        user._updated_at = utc_now()
        await self.user_repository.save(user)

        return user


class VerifyUserEmailUseCase:
    """Use case for verifying user email."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId) -> UserEntity:
        """
        Verify user email address.

        Args:
            user_id: User identifier

        Returns:
            UserEntity with verified email

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.verify_email()
        user._updated_at = utc_now()
        await self.user_repository.save(user)

        return user


class GetUserUseCase:
    """Use case for retrieving a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId) -> UserEntity | None:
        """
        Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            UserEntity if found, None otherwise
        """
        return await self.user_repository.get_by_id(user_id)
