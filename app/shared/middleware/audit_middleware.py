"""
Audit Middleware

FastAPI middleware for automatic audit logging of HTTP requests.
"""

import asyncio
import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.application.use_cases.audit_use_cases import LogAuditActionUseCase
from app.core.database import AsyncSessionLocal
from app.domain.enums import AuditActionType
from app.domain.value_objects.core import TenantId, UserId

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically logs HTTP requests as audit entries.

    This captures:
    - Request method and path
    - User ID (from request state or headers)
    - IP address
    - User agent
    - Response status
    """

    def __init__(self, app: ASGIApp, audit_repository_factory: Callable):
        """
        Initialize audit middleware.

        Args:
            app: ASGI application
            audit_repository_factory: Factory function to create audit repository
        """
        super().__init__(app)
        self.audit_repository_factory = audit_repository_factory

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit entry.

        Skips audit logging for:
        - Health checks
        - Audit endpoints themselves (to avoid recursion)
        - OPTIONS requests
        """
        # Skip audit logging for certain paths
        if self._should_skip_audit(request):
            return await call_next(request)

        # Extract context
        tenant_id = self._extract_tenant_id(request)
        user_id = self._extract_user_id(request)
        ip_address = self._extract_ip_address(request)
        user_agent = request.headers.get("user-agent")

        # Determine action type from HTTP method
        action_type = self._map_http_method_to_action(request.method)

        # Determine resource type from path
        resource_type, resource_id = self._extract_resource_info(request)

        # Process request
        response = await call_next(request)

        # Fire-and-forget audit logging (doesn't block response)
        if tenant_id:
            asyncio.create_task(
                self._log_audit_entry(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    request=request,
                    response=response,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )

        return response

    def _should_skip_audit(self, request: Request) -> bool:
        """Check if audit logging should be skipped for this request."""
        path = request.url.path

        # Skip health checks
        if path in ["/", "/health", "/docs", "/openapi.json", "/redoc"]:
            return True

        # Skip audit endpoints to avoid recursion
        if path.startswith("/audit"):
            return True

        # Skip OPTIONS requests
        if request.method == "OPTIONS":
            return True

        return False

    def _extract_tenant_id(self, request: Request) -> str | None:
        """Extract tenant ID from request."""
        # Try query parameter first
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id

        # Try header
        tenant_id = request.headers.get("x-tenant-id")
        if tenant_id:
            return tenant_id

        # Try path parameter (for routes like /tenants/{tenant_id}/...)
        if "tenant_id" in request.path_params:
            return request.path_params["tenant_id"]

        return None

    def _extract_user_id(self, request: Request) -> str | None:
        """Extract user ID from request."""
        # Try from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return request.state.user_id

        # Try header
        user_id = request.headers.get("x-user-id")
        if user_id:
            return user_id

        return None

    def _extract_ip_address(self, request: Request) -> str | None:
        """Extract IP address from request."""
        # Check for forwarded IP
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to client host
        if request.client:
            return request.client.host

        return None

    def _map_http_method_to_action(self, method: str) -> AuditActionType:
        """Map HTTP method to audit action type."""
        mapping = {
            "GET": AuditActionType.LIST,
            "POST": AuditActionType.CREATE,
            "PUT": AuditActionType.UPDATE,
            "PATCH": AuditActionType.UPDATE,
            "DELETE": AuditActionType.DELETE,
        }
        return mapping.get(method, AuditActionType.LIST)

    def _extract_resource_info(self, request: Request) -> tuple[str, str | None]:
        """
        Extract resource type and ID from request path.

        Returns:
            Tuple of (resource_type, resource_id)
        """
        path = request.url.path.strip("/")
        parts = path.split("/")

        # Map common paths to resource types
        resource_map = {
            "tenants": "Tenant",
            "persons": "Person",
            "clients": "Client",
            "contracts": "Contract",
            "services": "Service",
            "service-sessions": "ServiceSession",
            "users": "User",
        }

        # Find resource type
        resource_type = "Unknown"
        resource_id = None

        for i, part in enumerate(parts):
            if part in resource_map:
                resource_type = resource_map[part]
                # Check if next part is an ID (not a known action)
                if i + 1 < len(parts):
                    next_part = parts[i + 1]
                    # Skip known action paths
                    if next_part not in [
                        "activate",
                        "deactivate",
                        "suspend",
                        "terminate",
                        "archive",
                        "restore",
                        "verify",
                        "sign",
                        "renew",
                        "complete",
                        "cancel",
                        "reschedule",
                        "no-show",
                        "stats",
                        "children",
                        "check-code",
                        "check-name",
                    ]:
                        resource_id = next_part
                break

        return resource_type, resource_id

    async def _log_audit_entry(
        self,
        tenant_id: str,
        user_id: str | None,
        action_type: AuditActionType,
        resource_type: str,
        resource_id: str | None,
        request: Request,
        response: Response,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        """
        Background task to log audit entry.

        This runs asynchronously and doesn't block the HTTP response.
        All exceptions are caught and logged to prevent crashes.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            action_type: Audit action type
            resource_type: Resource type
            resource_id: Resource identifier
            request: FastAPI request
            response: FastAPI response
            ip_address: Client IP address
            user_agent: Client user agent
        """
        try:
            async with AsyncSessionLocal() as db:
                audit_repo = self.audit_repository_factory(db)
                log_use_case = LogAuditActionUseCase(audit_repo)

                # Log audit entry (may return None if filtered)
                audit_log = await log_use_case.execute(
                    tenant_id=TenantId(tenant_id),
                    action_type=action_type,
                    resource_type=resource_type,
                    user_id=UserId(user_id) if user_id else None,
                    resource_id=resource_id,
                    description=f"{request.method} {request.url.path}",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                        "query_params": dict(request.query_params),
                    },
                )
                # Only commit if audit log was created (not filtered)
                if audit_log is not None:
                    await db.commit()
        except Exception:
            # Log error but don't fail the request
            # Include context for debugging
            # logger.exception() automatically includes exception traceback
            logger.exception(
                "Failed to log audit entry for %s %s (tenant_id=%s, user_id=%s, action_type=%s)",
                request.method,
                request.url.path,
                tenant_id,
                user_id,
                action_type.value,
                extra={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "action_type": action_type.value,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "method": request.method,
                    "path": str(request.url.path),
                },
            )
