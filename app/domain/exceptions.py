"""
Domain exceptions for the Evexía application.

This module defines domain-level exceptions that represent business rule violations.
These exceptions are independent of infrastructure concerns.
"""

from typing import Any


class EvexiaException(Exception):
    """
    Base exception for all Evexía application errors.

    All custom exceptions should inherit from this class to allow
    for consistent error handling and logging.

    Attributes:
        message: Human-readable error description
        error_code: Machine-readable error code for API responses
        details: Additional error context
        http_status: HTTP status code for API responses (default 400)
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        http_status: int = 400,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def to_api_response(
        self,
        path: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Build API error body in the same shape as create_error_response.
        Used by the single exception handler for consistent JSON responses.
        """
        details_list: list[dict[str, Any]] | None = None
        if self.details:
            details_list = [
                {"field": k, "message": str(v), "code": None}
                for k, v in self.details.items()
            ]
        return {
            "error": self.error_code,
            "message": self.message,
            **({"details": details_list} if details_list else {}),
            **({"path": path} if path is not None else {}),
            **({"request_id": request_id} if request_id is not None else {}),
        }


class ValidationException(EvexiaException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        details = {"field": field} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details, http_status=422)


class AuthenticationException(EvexiaException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", http_status=401)


class AuthorizationException(EvexiaException):
    """Raised when user lacks required permissions."""

    def __init__(self, resource: str, action: str):
        message = f"Permission denied: {action} on {resource}"
        super().__init__(
            message, "AUTHORIZATION_ERROR", {"resource": resource, "action": action}, http_status=403
        )


class TenantNotFoundException(EvexiaException):
    """Raised when tenant is not found."""

    def __init__(self, tenant_id: str):
        super().__init__(
            f"Tenant not found: {tenant_id}",
            "TENANT_NOT_FOUND",
            {"tenant_id": tenant_id},
            http_status=404,
        )


class ResourceNotFoundException(EvexiaException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            "RESOURCE_NOT_FOUND",
            {"resource_type": resource_type, "resource_id": resource_id},
            http_status=404,
        )


class EventChainBrokenException(EvexiaException):
    """Raised when event chain integrity is violated."""

    def __init__(self, subject_id: str, event_id: str, reason: str):
        super().__init__(
            f"Event chain broken for subject {subject_id}",
            "CHAIN_INTEGRITY_ERROR",
            {"subject_id": subject_id, "event_id": event_id, "reason": reason},
        )


class SchemaValidationException(EvexiaException):
    """Raised when schema validation fails."""

    def __init__(self, schema_type: str, validation_errors: list[Any]):
        super().__init__(
            f"Schema validation failed for {schema_type}",
            "SCHEMA_VALIDATION_ERROR",
            {"schema_type": schema_type, "errors": validation_errors},
        )


class PermissionDeniedError(EvexiaException):
    """Permission denied - user lacks required permission."""

    def __init__(
        self,
        message: str = "Permission denied",
        resource: str | None = None,
        action: str | None = None,
    ):
        details: dict[str, Any] = {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action
        super().__init__(message, "PERMISSION_DENIED", details, http_status=403)


class DomainError(EvexiaException):
    """Raised when a domain rule is violated."""
    
    def __init__(self, message: str):
        super().__init__(message, "DOMAIN_ERROR")


class InvariantViolation(EvexiaException):
    """Raised when an entity invariant is violated."""
    
    def __init__(self, message: str):
        super().__init__(message, "INVARIANT_VIOLATION")


class SubscriptionLimitError(EvexiaException):
    """Raised when tenant subscription limit is reached (e.g. max users or max clients)."""

    def __init__(self, message: str = "Subscription limit reached"):
        super().__init__(message, "SUBSCRIPTION_LIMIT", http_status=403)
