"""
FastAPI Application

Main application entry point.
"""

from fastapi import FastAPI

from app.api.routes import tenants_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="EAP Platform API",
)

# Include routers
app.include_router(tenants_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}