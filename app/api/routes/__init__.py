"""
API Routes

FastAPI route handlers.
"""

from app.api.routes.tenants import router as tenants_router

__all__ = ["tenants_router"]
