"""
FastAPI Application

Main application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import (
    activities_router,
    audit_router,
    auth_router,
    client_tags_router,
    clients_router,
    contacts_router,
    contracts_router,
    documents_router,
    industries_router,
    kpis_router,
    persons_router,
    services_router,
    service_assignments_router,
    service_sessions_router,
    tenants_router,
    users_router,
)
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.domain.exceptions import (
    DomainError,
    ResourceNotFoundException,
    AuthorizationException,
    AuthenticationException,
    ValidationException,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Register event handlers
    from app.shared.events.handlers import register_default_handlers
    register_default_handlers()
    logger.info("Event handlers registered")
    
    yield
    
    # Cleanup
    from app.shared.events.event_bus import event_bus
    event_bus.clear_handlers()
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evexía API - Employee Assistance Program Management",
    lifespan=lifespan,
)

# =============================================================================
# MIDDLEWARE
# =============================================================================

# Rate Limiting Middleware (applied first, checked last)
from app.shared.middleware.rate_limit import RateLimitMiddleware, RateLimitConfig

if not settings.is_development:
    # Only enable rate limiting in non-development environments
    app.add_middleware(
        RateLimitMiddleware,
        config=RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=10,
        ),
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

from app.shared.utils.errors import create_error_response
from app.shared.utils.http_errors import get_error_status_code


@app.exception_handler(ResourceNotFoundException)
async def not_found_exception_handler(request: Request, exc: ResourceNotFoundException):
    """Handle ResourceNotFoundException exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(
            error=exc.error_code,
            message=exc.message,
            details=[{"field": k, "message": str(v), "code": None} for k, v in exc.details.items()] if exc.details else None,
            path=str(request.url.path),
        ),
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    """Handle AuthorizationException exceptions."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=create_error_response(
            error=exc.error_code,
            message=exc.message,
            details=[{"field": k, "message": str(v), "code": None} for k, v in exc.details.items()] if exc.details else None,
            path=str(request.url.path),
        ),
    )


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    """Handle AuthenticationException exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=create_error_response(
            error=exc.error_code,
            message=exc.message,
            path=str(request.url.path),
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle ValidationException exceptions."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            error=exc.error_code,
            message=exc.message,
            details=[{"field": k, "message": str(v), "code": None} for k, v in exc.details.items()] if exc.details else None,
            path=str(request.url.path),
        ),
    )


@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    """Handle DomainError exceptions."""
    # Determine appropriate status code based on error message
    status_code = get_error_status_code(exc.message)
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(
            error=exc.error_code,
            message=exc.message,
            path=str(request.url.path),
        ),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error="VALUE_ERROR",
            message=str(exc),
            path=str(request.url.path),
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error="INTERNAL_ERROR",
            message="An internal server error occurred",
            path=str(request.url.path),
        ),
    )


# =============================================================================
# ROUTERS
# =============================================================================

app.include_router(auth_router)  # Authentication routes (login, etc.)
app.include_router(tenants_router)
app.include_router(users_router)
app.include_router(persons_router)
app.include_router(clients_router)
app.include_router(industries_router)
app.include_router(client_tags_router)
app.include_router(contacts_router)
app.include_router(activities_router)
app.include_router(contracts_router)
app.include_router(services_router)
app.include_router(service_assignments_router)
app.include_router(service_sessions_router)
app.include_router(documents_router)
app.include_router(kpis_router)
app.include_router(audit_router)


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


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
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "database": "disconnected"},
        ) 