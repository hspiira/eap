"""
SQLAlchemy Models

Database models for persistence. These are data containers only - no business logic.
"""

from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)
from app.infrastructure.models.activity_model import ActivityModel
from app.infrastructure.models.audit_model import AuditLogModel, EntityChangeModel
from app.infrastructure.models.care_callback_model import (
    CareCallbackCampaignModel,
    OutreachRecordModel,
)
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.infrastructure.models.contact_model import ContactModel
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.critical_incident_model import CriticalIncidentModel
from app.infrastructure.models.diagnosis_model import DiagnosisModel, DiagnosisTypeModel
from app.infrastructure.models.document_model import DocumentModel
from app.infrastructure.models.industry_model import IndustryModel
from app.infrastructure.models.json_schemas import (
    DependentInfoDict,
    EmergencyContactDict,
    EmploymentInfoDict,
    LicenseInfoDict,
    ProviderProfileDict,
    StaffInfoDict,
)
from app.infrastructure.models.kpi_model import KPIAssignmentModel, KPIModel
from app.infrastructure.models.non_compete_clause_model import NonCompeteClauseModel
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.password_set_token_model import PasswordSetTokenModel
from app.infrastructure.models.report_model import (
    ReportRunModel,
    ReportTemplateModel,
)
from app.infrastructure.models.person_model import PersonModel
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.survey_model import (
    SurveyCampaignModel,
    SurveyResponseModel,
)
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.models.utilisation_event_model import UtilisationEventModel

__all__ = [
    "ActivityModel",
    "AuditLogModel",
    "Base",
    "CareCallbackCampaignModel",
    "ClientModel",
    "ClientTagModel",
    "ContactModel",
    "ContractModel",
    "CriticalIncidentModel",
    "CuidMixin",
    "DependentInfoDict",
    "DiagnosisModel",
    "DiagnosisTypeModel",
    "DocumentModel",
    "EmergencyContactDict",
    "EmploymentInfoDict",
    "EntityChangeModel",
    "EnumValueType",
    "IndustryModel",
    "KPIAssignmentModel",
    "KPIModel",
    "LicenseInfoDict",
    "NonCompeteClauseModel",
    "OutboxEventModel",
    "OutreachRecordModel",
    "PasswordSetTokenModel",
    "PersonModel",
    "ProviderProfileDict",
    "ReportRunModel",
    "ReportTemplateModel",
    "ServiceAssignmentModel",
    "ServiceModel",
    "ServiceSessionModel",
    "SoftDeleteMixin",
    "StaffInfoDict",
    "SurveyCampaignModel",
    "SurveyResponseModel",
    "TenantModel",
    "TenantMixin",
    "TimestampMixin",
    "UserModel",
    "UtilisationEventModel",
]
