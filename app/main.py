"""
FastAPI Application

Main application entry point. Kept minimal: lifespan, app creation,
registration of exception handlers, middleware, and routers; root endpoints only.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
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
