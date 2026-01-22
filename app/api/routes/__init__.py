"""
API Routes

FastAPI route handlers.
"""

from app.api.routes.persons import router as persons_router
from app.api.routes.tenants import router as tenants_router

__all__ = ["persons_router", "tenants_router"]
