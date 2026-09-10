"""
FastAPI Application

Main application entry point. Kept minimal: lifespan, app creation,
registration of exception handlers, middleware, and routers; root endpoints only.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.security import TokenData

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy import text

from app.api.routes import register_routers
from app.core.authorization import block_viewer_writes
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import setup_middleware
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.pages import render_root_page
from app.shared.utils.datetime import utc_now

configure_logging(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


async def _validate_active_user(request: Request, token_data: TokenData) -> None:
    """Validate that user and tenant exist and are active. Raises HTTP 401 if not."""
    from fastapi import HTTPException
    from starlette import status

    from app.core.database import AsyncSessionLocal
    from app.domain.enums import TenantStatus
    from app.domain.value_objects.core import TenantId, UserId
    from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl
    from app.infrastructure.repositories.user_repository import UserRepositoryImpl

    async with AsyncSessionLocal() as session:
        user_repo = UserRepositoryImpl(session)
        tenant_repo = TenantRepositoryImpl(session)
        user = await user_repo.get_by_id(UserId(token_data.user_id))
        if not user or not user.is_active():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        tenant = await tenant_repo.get_by_id(TenantId(token_data.tenant_id))
        if not tenant or tenant.status != TenantStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    from app.core.login_rate_limit import get_login_rate_limit_backend

    app.state.login_rate_limit_backend = get_login_rate_limit_backend(
        settings.LOGIN_RATE_LIMIT_BACKEND,
        settings.REDIS_URL or "",
    )
    if getattr(settings, "STRICT_ACTIVE_USER_CHECK", False):
        app.state.validate_active_user = _validate_active_user
    else:
        app.state.validate_active_user = None
    from app.shared.events.handlers import register_default_handlers

    register_default_handlers()
    logger.info("Event handlers registered")
    yield
    from app.shared.events.event_bus import event_bus

    event_bus.clear_handlers()
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evexía API - Employee Assistance Program Management",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    # Viewers are read-only, enforced once for every route rather than route by
    # route. See block_viewer_writes and its allowlist.
    dependencies=[Depends(block_viewer_writes)],
)

register_exception_handlers(app)
setup_middleware(app)
register_routers(app)


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Landing page with links to API documentation."""
    return HTMLResponse(content=render_root_page(settings.APP_NAME))


@app.get("/docs", include_in_schema=False)
def scalar_docs():
    """Serve Scalar API reference (replaces Swagger UI)."""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} API",
        scalar_proxy_url="https://proxy.scalar.com",
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "database": "disconnected"},
        )


@app.get("/health/outbox")
async def outbox_health():
    """Whether the outbox worker is keeping up.

    Reports unhealthy on the age of the oldest undelivered event, not on
    depth. Nothing watched this before, and the worker being stopped showed
    up only as an empty audit_logs that nothing reads.
    """
    try:
        async with AsyncSessionLocal() as session:
            backlog = await OutboxRepositoryImpl(session).backlog()
    except Exception as e:
        logger.error(f"Outbox health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unknown", "error": "backlog query failed"},
        )

    lag = backlog.age_seconds(now=utc_now())
    healthy = lag is None or lag <= settings.OUTBOX_MAX_LAG_SECONDS
    body = {
        "status": "ok" if healthy else "behind",
        "depth": backlog.depth,
        "failed": backlog.failed,
        "lag_seconds": int(lag) if lag is not None else None,
        "max_lag_seconds": settings.OUTBOX_MAX_LAG_SECONDS,
    }
    return body if healthy else JSONResponse(status_code=503, content=body)


@app.get("/metrics", include_in_schema=False)
async def metrics(request: Request):
    """
    Metrics endpoint (request count, 5xx count, uptime, last request latency).
    Returns JSON. For Prometheus, use an exporter or sidecar that consumes this.
    """
    from app.shared.middleware.metrics import get_metrics

    return get_metrics(request.app.state)
