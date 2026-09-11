"""
API Routes

FastAPI route handlers and router registration.
"""

from fastapi import FastAPI

from app.api.routes.activities import router as activities_router
from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.auth_azure import router as auth_azure_router
from app.api.routes.benchmark import router as benchmark_router
from app.api.routes.care_callbacks import router as care_callbacks_router
from app.api.routes.case_referral_sources import router as case_referral_sources_router
from app.api.routes.cases import router as cases_router
from app.api.routes.client_tags import router as client_tags_router
from app.api.routes.client_tiers import router as client_tiers_router
from app.api.routes.clients import router as clients_router
from app.api.routes.clinical_notes import router as clinical_notes_router
from app.api.routes.contacts import router as contacts_router
from app.api.routes.contracts import router as contracts_router
from app.api.routes.critical_incidents import router as critical_incidents_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.diagnoses import router as diagnoses_router
from app.api.routes.document_types import router as document_types_router
from app.api.routes.documents import router as documents_router
from app.api.routes.dsar import router as dsar_router
from app.api.routes.eap_programmes import router as eap_programmes_router
from app.api.routes.eligible_members import router as eligible_members_router
from app.api.routes.engagements import router as engagements_router
from app.api.routes.industries import router as industries_router
from app.api.routes.kpi_categories import router as kpi_categories_router
from app.api.routes.kpi_measurement_units import (
    router as kpi_measurement_units_router,
)
from app.api.routes.kpis import router as kpis_router
from app.api.routes.members import router as members_router
from app.api.routes.next_of_kin_relationships import (
    router as next_of_kin_relationships_router,
)
from app.api.routes.non_compete_clauses import router as non_compete_router
from app.api.routes.panel import router as panel_router
from app.api.routes.practitioner_imports import router as practitioner_imports_router
from app.api.routes.presenting_problems import router as presenting_problems_router
from app.api.routes.pricing import router as pricing_router
from app.api.routes.provider_affiliations import router as provider_affiliations_router
from app.api.routes.provider_organisations import router as provider_organisations_router
from app.api.routes.provider_specialties import router as provider_specialties_router
from app.api.routes.providers import router as providers_router
from app.api.routes.reports import router as reports_router
from app.api.routes.search import router as search_router
from app.api.routes.service_assignments import router as service_assignments_router
from app.api.routes.service_categories import router as service_categories_router
from app.api.routes.service_sessions import router as service_sessions_router
from app.api.routes.services import router as services_router
from app.api.routes.session_imports import router as session_imports_router
from app.api.routes.survey_sources import router as survey_sources_router
from app.api.routes.surveys import router as surveys_router
from app.api.routes.tenants import router as tenants_router
from app.api.routes.users import router as users_router
from app.api.routes.utilisation_event_types import (
    router as utilisation_event_types_router,
)


def register_routers(app: FastAPI) -> None:
    """Register all API routers on the FastAPI app."""
    app.include_router(auth_router)
    app.include_router(auth_azure_router)
    app.include_router(tenants_router)
    app.include_router(users_router)
    app.include_router(providers_router)
    app.include_router(provider_organisations_router)
    app.include_router(provider_affiliations_router)
    app.include_router(provider_specialties_router)
    app.include_router(session_imports_router)
    app.include_router(practitioner_imports_router)
    app.include_router(clients_router)
    app.include_router(industries_router)
    app.include_router(client_tags_router)
    app.include_router(client_tiers_router)
    app.include_router(contacts_router)
    app.include_router(activities_router)
    app.include_router(contracts_router)
    app.include_router(services_router)
    app.include_router(service_categories_router)
    app.include_router(service_assignments_router)
    app.include_router(service_sessions_router)
    app.include_router(documents_router)
    app.include_router(document_types_router)
    app.include_router(diagnoses_router)
    app.include_router(critical_incidents_router)
    app.include_router(non_compete_router)
    app.include_router(panel_router)
    app.include_router(reports_router)
    app.include_router(pricing_router)
    app.include_router(utilisation_event_types_router)
    app.include_router(care_callbacks_router)
    app.include_router(cases_router)
    app.include_router(case_referral_sources_router)
    app.include_router(presenting_problems_router)
    app.include_router(clinical_notes_router)
    app.include_router(surveys_router)
    app.include_router(survey_sources_router)
    app.include_router(engagements_router)
    app.include_router(dsar_router)
    app.include_router(benchmark_router)
    app.include_router(eligible_members_router)
    app.include_router(members_router)
    app.include_router(next_of_kin_relationships_router)
    app.include_router(eap_programmes_router)
    app.include_router(kpis_router)
    app.include_router(kpi_categories_router)
    app.include_router(kpi_measurement_units_router)
    app.include_router(audit_router)
    app.include_router(search_router)
    app.include_router(dashboard_router)


__all__ = [
    "activities_router",
    "audit_router",
    "auth_router",
    "auth_azure_router",
    "benchmark_router",
    "care_callbacks_router",
    "case_referral_sources_router",
    "cases_router",
    "clinical_notes_router",
    "client_tags_router",
    "client_tiers_router",
    "clients_router",
    "contacts_router",
    "contracts_router",
    "critical_incidents_router",
    "dashboard_router",
    "diagnoses_router",
    "document_types_router",
    "documents_router",
    "dsar_router",
    "eap_programmes_router",
    "eligible_members_router",
    "engagements_router",
    "industries_router",
    "kpi_categories_router",
    "kpi_measurement_units_router",
    "kpis_router",
    "members_router",
    "next_of_kin_relationships_router",
    "non_compete_router",
    "panel_router",
    "presenting_problems_router",
    "provider_affiliations_router",
    "provider_organisations_router",
    "provider_specialties_router",
    "practitioner_imports_router",
    "providers_router",
    "pricing_router",
    "utilisation_event_types_router",
    "register_routers",
    "reports_router",
    "search_router",
    "service_categories_router",
    "services_router",
    "service_assignments_router",
    "service_sessions_router",
    "surveys_router",
    "survey_sources_router",
    "session_imports_router",
    "tenants_router",
    "users_router",
]
