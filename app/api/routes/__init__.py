"""
API Routes

FastAPI route handlers.
"""

from app.api.routes.audit import router as audit_router
from app.api.routes.clients import router as clients_router
from app.api.routes.contracts import router as contracts_router
from app.api.routes.documents import router as documents_router
from app.api.routes.persons import router as persons_router
from app.api.routes.services import router as services_router
from app.api.routes.service_sessions import router as service_sessions_router
from app.api.routes.tenants import router as tenants_router
from app.api.routes.users import router as users_router

__all__ = [
    "audit_router",
    "clients_router",
    "contracts_router",
    "documents_router",
    "persons_router",
    "services_router",
    "service_sessions_router",
    "tenants_router",
    "users_router",
]
