"""
User Use Cases

Application services for User aggregate operations.
"""

from app.domain.entities.user import UserEntity
from app.domain.enums import Language, UserStatus
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
        existing = await self.user_repository.get_by_email(email, tenant_id)
        if existing:
            raise ValueError(f"User with email {email.value} already exists")

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
            raise ValueError("User not found")

        user.verify_email()
        user._updated_at = utc_now()
        await self.user_repository.save(user)

        return user


class SuspendUserUseCase:
    """Use case for suspending a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId, reason: str) -> UserEntity:
        """
        Suspend a user.

        Args:
            user_id: User identifier
            reason: Suspension reason

        Returns:
            Suspended UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If suspension is invalid
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.suspend(reason)
        user._updated_at = utc_now()
        await self.user_repository.save(user)

        return user


class BanUserUseCase:
    """Use case for banning a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId, reason: str) -> UserEntity:
        """
        Ban a user.

        Args:
            user_id: User identifier
            reason: Ban reason

        Returns:
            Banned UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If ban is invalid
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.ban(reason)
        user._updated_at = utc_now()
        await self.user_repository.save(user)

        return user


class DeactivateUserUseCase:
    """Use case for deactivating a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self, user_id: UserId, reason: str | None = None
    ) -> UserEntity:
        """
        Deactivate a user.

        Args:
            user_id: User identifier
            reason: Deactivation reason (optional)

        Returns:
            Deactivated UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If deactivation is invalid
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.deactivate(reason)
        user._updated_at = utc_now()
        await self.user_repository.save(user)

        return user


class TerminateUserUseCase:
    """Use case for terminating a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId, reason: str) -> UserEntity:
        """
        Terminate a user.

        Args:
            user_id: User identifier
            reason: Termination reason

        Returns:
            Terminated UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If termination is invalid
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.terminate(reason)
        user._updated_at = utc_now()
        await self.user_repository.save(user)

        return user


class UpdateUserPasswordUseCase:
    """Use case for updating user password."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId, password_hash: str) -> UserEntity:
        """
        Update user password.

        Args:
            user_id: User identifier
            password_hash: Hashed password

        Returns:
            Updated UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If update is invalid
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.update_password(password_hash)
        await self.user_repository.save(user)

        return user


class UpdateUserPreferencesUseCase:
    """Use case for updating user preferences."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        user_id: UserId,
        preferred_language: Language | None = None,
        timezone: str | None = None,
    ) -> UserEntity:
        """
        Update user preferences.

        Args:
            user_id: User identifier
            preferred_language: Preferred language (optional)
            timezone: User timezone (optional)

        Returns:
            Updated UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If update is invalid
        """
        from app.domain.enums import Language

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.update_preferences(preferred_language, timezone)
        await self.user_repository.save(user)

        return user


class EnableTwoFactorUseCase:
    """Use case for enabling two-factor authentication."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId) -> UserEntity:
        """
        Enable two-factor authentication.

        Args:
            user_id: User identifier

        Returns:
            Updated UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If enable is invalid
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.enable_two_factor()
        await self.user_repository.save(user)

        return user


class DisableTwoFactorUseCase:
    """Use case for disabling two-factor authentication."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId) -> UserEntity:
        """
        Disable two-factor authentication.

        Args:
            user_id: User identifier

        Returns:
            Updated UserEntity

        Raises:
            ValueError: If user not found
            DomainError: If disable is invalid
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.disable_two_factor()
        await self.user_repository.save(user)

        return user


class RecordUserLoginUseCase:
    """Use case for recording user login."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UserId) -> UserEntity:
        """
        Record user login.

        Args:
            user_id: User identifier

        Returns:
            Updated UserEntity

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id.value} not found")

        user.record_login()
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
