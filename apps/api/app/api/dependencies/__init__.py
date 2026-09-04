"""FastAPI DI factories, split by bounded context.

Composition root: each factory wires an infrastructure repository into a
route via Depends(...). Re-exported here so
``from app.api.dependencies import X`` keeps working unchanged for the
31 route modules that import this way.
"""

from app.api.dependencies.audit import (
    get_audit_event_handler,
    get_audit_repository,
    get_outbox_repository,
)
from app.api.dependencies.clinical import (
    get_authorization_repository,
    get_case_repository,
    get_clinical_note_repository,
    get_clinical_subject_repository,
    get_eap_programme_repository,
    get_eligible_member_clinical_link_repository,
    get_eligible_member_repository,
)
from app.api.dependencies.commercial import get_contract_repository
from app.api.dependencies.consultancy import get_engagement_repository
from app.api.dependencies.crisis import (
    get_critical_incident_repository,
)
from app.api.dependencies.delivery import (
    get_diagnosis_repository,
    get_document_repository,
    get_kpi_assignment_repository,
    get_kpi_repository,
    get_service_assignment_repository,
    get_service_repository,
    get_service_session_repository,
)
from app.api.dependencies.identity import (
    get_contact_repository,
    get_person_repository,
    get_user_repository,
)
from app.api.dependencies.organization import (
    get_activity_repository,
    get_client_alias_repository,
    get_client_repository,
    get_client_tag_repository,
    get_industry_repository,
)
from app.api.dependencies.outreach import (
    get_care_callback_campaign_repository,
    get_outreach_record_repository,
    get_survey_campaign_repository,
    get_survey_response_repository,
)
from app.api.dependencies.pagination import PageParams, pagination
from app.api.dependencies.privacy import (
    get_benchmark_collector,
    get_benchmark_consent_repository,
    get_dsar_collector,
    get_dsar_request_repository,
    get_dsar_tombstoner,
)
from app.api.dependencies.provider import get_non_compete_clause_repository
from app.api.dependencies.reporting import (
    get_report_query_runner,
    get_report_run_repository,
    get_report_template_repository,
    get_utilisation_event_repository,
)
from app.api.dependencies.tenancy import (
    get_password_set_token_repository,
    get_refresh_token_repository,
    get_tenant_repository,
)

__all__ = [
    "PageParams",
    "pagination",
    "get_activity_repository",
    "get_client_alias_repository",
    "get_audit_event_handler",
    "get_audit_repository",
    "get_authorization_repository",
    "get_benchmark_collector",
    "get_benchmark_consent_repository",
    "get_care_callback_campaign_repository",
    "get_case_repository",
    "get_client_repository",
    "get_client_tag_repository",
    "get_clinical_note_repository",
    "get_clinical_subject_repository",
    "get_contact_repository",
    "get_contract_repository",
    "get_critical_incident_repository",
    "get_diagnosis_repository",
    "get_document_repository",
    "get_dsar_collector",
    "get_dsar_request_repository",
    "get_dsar_tombstoner",
    "get_eap_programme_repository",
    "get_eligible_member_clinical_link_repository",
    "get_eligible_member_repository",
    "get_engagement_repository",
    "get_industry_repository",
    "get_kpi_assignment_repository",
    "get_kpi_repository",
    "get_non_compete_clause_repository",
    "get_outbox_repository",
    "get_outreach_record_repository",
    "get_password_set_token_repository",
    "get_person_repository",
    "get_refresh_token_repository",
    "get_report_query_runner",
    "get_report_run_repository",
    "get_report_template_repository",
    "get_service_assignment_repository",
    "get_service_repository",
    "get_service_session_repository",
    "get_survey_campaign_repository",
    "get_survey_response_repository",
    "get_tenant_repository",
    "get_user_repository",
    "get_utilisation_event_repository",
]
