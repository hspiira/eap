"""
API Routes

FastAPI route handlers and router registration.
"""

from fastapi import FastAPI

from app.api.routes.activities import router as activities_router
from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.care_callbacks import router as care_callbacks_router
from app.api.routes.client_tags import router as client_tags_router
from app.api.routes.clients import router as clients_router
from app.api.routes.contacts import router as contacts_router
from app.api.routes.contracts import router as contracts_router
from app.api.routes.critical_incidents import router as critical_incidents_router
from app.api.routes.diagnoses import router as diagnoses_router
from app.api.routes.documents import router as documents_router
from app.api.routes.industries import router as industries_router
from app.api.routes.kpis import router as kpis_router
from app.api.routes.non_compete_clauses import router as non_compete_router
from app.api.routes.persons import router as persons_router
from app.api.routes.pricing import router as pricing_router
from app.api.routes.reports import router as reports_router
from app.api.routes.services import router as services_router
from app.api.routes.service_assignments import router as service_assignments_router
from app.api.routes.service_sessions import router as service_sessions_router
from app.api.routes.surveys import router as surveys_router
from app.api.routes.tenants import router as tenants_router
from app.api.routes.users import router as users_router


def register_routers(app: FastAPI) -> None:
    """Register all API routers on the FastAPI app."""
    app.include_router(auth_router)
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
    app.include_router(diagnoses_router)
    app.include_router(critical_incidents_router)
    app.include_router(non_compete_router)
    app.include_router(reports_router)
    app.include_router(pricing_router)
    app.include_router(care_callbacks_router)
    app.include_router(surveys_router)
    app.include_router(kpis_router)
    app.include_router(audit_router)


__all__ = [
    "activities_router",
    "audit_router",
    "auth_router",
    "care_callbacks_router",
    "client_tags_router",
    "clients_router",
    "contacts_router",
    "contracts_router",
    "critical_incidents_router",
    "diagnoses_router",
    "documents_router",
    "industries_router",
    "kpis_router",
    "non_compete_router",
    "persons_router",
    "pricing_router",
    "register_routers",
    "reports_router",
    "services_router",
    "service_assignments_router",
    "service_sessions_router",
    "surveys_router",
    "tenants_router",
    "users_router",
]
