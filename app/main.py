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

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy import text

from app.api.routes import register_routers
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import setup_middleware
from app.pages import render_root_page

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _validate_active_user(request: Request, token_data: "TokenData") -> None:
    """Validate that user and tenant exist and are active. Raises HTTP 401 if not."""
    from fastapi import HTTPException
    from starlette import status
    from app.core.database import AsyncSessionLocal
    from app.infrastructure.repositories.user_repository import UserRepositoryImpl
    from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl
    from app.domain.value_objects.core import UserId, TenantId
    from app.domain.enums import TenantStatus
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
        from app.core.security import TokenData
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


@app.get("/metrics", include_in_schema=False)
async def metrics(request: Request):
    """
    Metrics endpoint (request count, 5xx count, uptime, last request latency).
    Returns JSON. For Prometheus, use an exporter or sidecar that consumes this.
    """
    from app.shared.middleware.metrics import get_metrics
    return get_metrics(request.app.state)
