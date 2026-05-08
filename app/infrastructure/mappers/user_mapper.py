"""
User Mapper

Converts between UserEntity (domain) and UserModel (persistence).
"""

from app.domain.entities.user import UserEntity
from app.domain.enums import Language, TenantRole, UserStatus
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
        role = TenantRole(model.role) if getattr(model, "role", None) is not None else TenantRole.USER

        # Create entity
        return UserEntity(
            _id=user_id,
            _tenant_id=tenant_id,
            _email=email,
            _password_hash=model.password_hash,
            _email_verified_at=ensure_utc(model.email_verified_at),
            _status=status,
            _status_changed_at=ensure_utc(model.status_changed_at),
            _preferred_language=preferred_language,
            _timezone=model.timezone,
            _is_two_factor_enabled=model.is_two_factor_enabled,
            _last_login_at=ensure_utc(model.last_login_at),
            _role=role,
            _failed_login_count=getattr(model, "failed_login_count", 0) or 0,
            _locked_until=ensure_utc(getattr(model, "locked_until", None)),
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at),
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
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            email=entity._email.value,
            password_hash=entity._password_hash,
            email_verified_at=entity._email_verified_at,
            status=entity._status,
            status_changed_at=entity._status_changed_at,
            preferred_language=entity._preferred_language
            if entity._preferred_language
            else None,
            timezone=entity._timezone,
            is_two_factor_enabled=entity._is_two_factor_enabled,
            last_login_at=entity._last_login_at,
            role=entity._role,
            failed_login_count=entity._failed_login_count,
            locked_until=entity._locked_until,
            deleted_at=entity._deleted_at,
        )

        # Set updated_at if provided (otherwise TimestampMixin will handle it)
        if entity._updated_at:
            model.updated_at = entity._updated_at

        return model
