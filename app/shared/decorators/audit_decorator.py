"""
Audit Decorator

Decorator for automatically auditing use case executions.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from app.domain.repositories.audit_repository import AuditRepository
from app.domain.value_objects.core import TenantId, UserId

T = TypeVar("T")


def audit_use_case(
    audit_repository_factory: Callable[[], AuditRepository],
    tenant_id_extractor: Callable[[Any], TenantId | None] | None = None,
    user_id_extractor: Callable[[Any], UserId | None] | None = None,
):
    """
    Decorator to automatically audit use case executions.
    
    Usage:
        @audit_use_case(get_audit_repository)
        async def execute(self, ...):
            ...
    
    Args:
        audit_repository_factory: Factory function to create audit repository
        tenant_id_extractor: Function to extract tenant_id from use case args
        user_id_extractor: Function to extract user_id from use case args
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            # Execute use case
            result = await func(self, *args, **kwargs)

            # Extract context
            tenant_id = None
            if tenant_id_extractor:
                tenant_id = tenant_id_extractor(*args, **kwargs)
            else:
                # Try to find tenant_id in args/kwargs
                for arg in args:
                    if hasattr(arg, "value") and "TenantId" in str(type(arg)):
                        tenant_id = arg
                        break
                if not tenant_id:
                    tenant_id = kwargs.get("tenant_id")

            user_id = None
            if user_id_extractor:
                user_id = user_id_extractor(*args, **kwargs)
            else:
                # Try to find user_id in args/kwargs
                for arg in args:
                    if hasattr(arg, "value") and "UserId" in str(type(arg)):
                        user_id = arg
                        break
                if not user_id:
                    user_id = kwargs.get("user_id")

            # Process events if result is an entity with events
            if hasattr(result, "_events") and result.events:
                # Get audit repository (would need db session - this is simplified)
                # In practice, you'd pass db session through context
                # For now, this is a placeholder showing the pattern
                pass

            return result

        return wrapper

    return decorator
