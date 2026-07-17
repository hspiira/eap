"""
User Mapper

Converts between UserEntity (domain) and UserModel (persistence).
"""

from app.domain.entities.user import UserEntity
from app.domain.enums import AuthProvider, Language, TenantRole, UserStatus
from app.domain.value_objects.core import Email, TenantId, UserId
from app.infrastructure.models.user_model import UserModel
from app.shared.utils.datetime import ensure_utc


class UserMapper:
    """Mapper for UserEntity ↔ UserModel conversion"""

    @staticmethod
    def to_entity(model: UserModel) -> UserEntity:
        """
        Convert database model to domain entity.

        Args:
            model: UserModel from database

        Returns:
            UserEntity with business logic
        """
        # Reconstruct value objects
        user_id = UserId(model.id)
        tenant_id = TenantId(model.tenant_id)
        email = Email(model.email)

        # Reconstruct enums
        status = UserStatus(model.status)
        preferred_language = (
            Language(model.preferred_language) if model.preferred_language else None
        )
        role = (
            TenantRole(model.role) if getattr(model, "role", None) is not None else TenantRole.USER
        )
        auth_provider = (
            AuthProvider(model.auth_provider)
            if getattr(model, "auth_provider", None)
            else AuthProvider.PASSWORD
        )

        # Create entity
        return UserEntity(
            id=user_id,
            tenant_id=tenant_id,
            email=email,
            _password_hash=model.password_hash,
            email_verified_at=ensure_utc(model.email_verified_at),
            status=status,
            status_changed_at=ensure_utc(model.status_changed_at),
            preferred_language=preferred_language,
            timezone=model.timezone,
            is_two_factor_enabled=model.is_two_factor_enabled,
            last_login_at=ensure_utc(model.last_login_at),
            role=role,
            failed_login_count=getattr(model, "failed_login_count", 0) or 0,
            locked_until=ensure_utc(getattr(model, "locked_until", None)),
            azure_oid=model.azure_oid,
            display_name=getattr(model, "display_name", None),
            auth_provider=auth_provider,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at),
        )

    @staticmethod
    def to_model(entity: UserEntity) -> UserModel:
        """
        Convert domain entity to database model.

        Args:
            entity: UserEntity with business logic

        Returns:
            UserModel for persistence
        """
        # Create model
        # Note: created_at and updated_at are handled by TimestampMixin
        model = UserModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            email=entity.email.value,
            password_hash=entity._password_hash,
            email_verified_at=entity.email_verified_at,
            status=entity.status,
            status_changed_at=entity.status_changed_at,
            preferred_language=entity.preferred_language if entity.preferred_language else None,
            timezone=entity.timezone,
            is_two_factor_enabled=entity.is_two_factor_enabled,
            last_login_at=entity.last_login_at,
            role=entity.role,
            failed_login_count=entity.failed_login_count,
            locked_until=entity.locked_until,
            azure_oid=entity.azure_oid,
            display_name=entity.display_name,
            auth_provider=entity.auth_provider,
            deleted_at=entity.deleted_at,
        )

        # Set updated_at if provided (otherwise TimestampMixin will handle it)
        if entity.updated_at:
            model.updated_at = entity.updated_at

        return model
