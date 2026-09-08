"""
SQLAlchemy Models

Database models for persistence. These are data containers only - no business logic.
"""

from app.infrastructure.models.activity_model import ActivityModel
from app.infrastructure.models.audit_model import AuditLogModel, EntityChangeModel
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)
from app.infrastructure.models.benchmark_consent_model import BenchmarkConsentModel
from app.infrastructure.models.care_callback_model import (
    CareCallbackCampaignModel,
    OutreachRecordModel,
)
from app.infrastructure.models.case_model import CaseModel
from app.infrastructure.models.client_alias_model import ClientAliasModel
from app.infrastructure.models.client_import_job_model import ClientImportJobModel
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.client_saved_view_model import ClientSavedViewModel
from app.infrastructure.models.client_tag_assignment_model import ClientTagAssignmentModel
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.infrastructure.models.clinical_note_model import ClinicalNoteModel
from app.infrastructure.models.contact_model import ContactModel
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.critical_incident_model import CriticalIncidentModel
from app.infrastructure.models.diagnosis_model import (
    DiagnosisAliasModel,
    DiagnosisModel,
    DiagnosisTypeModel,
    TenantDiagnosisSettingModel,
)
from app.infrastructure.models.document_model import DocumentModel
from app.infrastructure.models.dsar_model import DSARRequestModel
from app.infrastructure.models.eap_programme_model import (
    AuthorizationModel,
    EAPProgrammeModel,
)
from app.infrastructure.models.eligible_member_model import (
    ClinicalSubjectModel,
    EligibleMemberClinicalLinkModel,
    EligibleMemberModel,
)
from app.infrastructure.models.engagement_model import EngagementModel
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
from app.infrastructure.models.member_next_of_kin_model import MemberNextOfKinModel
from app.infrastructure.models.non_compete_clause_model import NonCompeteClauseModel
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.password_set_token_model import PasswordSetTokenModel
from app.infrastructure.models.person_model import PersonModel
from app.infrastructure.models.practitioner_import_model import (
    PractitionerImportBatchModel,
    PractitionerImportRowModel,
)
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_alias_model import ProviderAliasModel
from app.infrastructure.models.provider_engagement_document_model import (
    ProviderEngagementDocumentModel,
)
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.provider_specialty_model import (
    ProviderSpecialtyLinkModel,
    ProviderSpecialtyModel,
)
from app.infrastructure.models.report_model import (
    ReportRunModel,
    ReportTemplateModel,
)
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.infrastructure.models.service_category_model import ServiceCategoryModel
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)
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
    "AuthorizationModel",
    "Base",
    "BenchmarkConsentModel",
    "CareCallbackCampaignModel",
    "CaseModel",
    "ClinicalNoteModel",
    "ClinicalSubjectModel",
    "EAPProgrammeModel",
    "ClientModel",
    "ClientImportJobModel",
    "ClientSavedViewModel",
    "ClientAliasModel",
    "ClientTagModel",
    "ClientTagAssignmentModel",
    "ContactModel",
    "ContractModel",
    "CriticalIncidentModel",
    "CuidMixin",
    "DependentInfoDict",
    "DSARRequestModel",
    "DiagnosisModel",
    "EligibleMemberClinicalLinkModel",
    "EligibleMemberModel",
    "MemberNextOfKinModel",
    "DiagnosisAliasModel",
    "DiagnosisTypeModel",
    "TenantDiagnosisSettingModel",
    "DocumentModel",
    "EmergencyContactDict",
    "EmploymentInfoDict",
    "EngagementModel",
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
    "PractitionerImportBatchModel",
    "PractitionerImportRowModel",
    "ProviderAffiliationModel",
    "ProviderAliasModel",
    "ProviderEngagementDocumentModel",
    "ProviderModel",
    "ProviderOrganisationModel",
    "ProviderSpecialtyLinkModel",
    "ProviderSpecialtyModel",
    "ProviderProfileDict",
    "ReportRunModel",
    "ReportTemplateModel",
    "ServiceAssignmentModel",
    "ServiceCategoryModel",
    "ServiceModel",
    "ServiceSessionModel",
    "SessionImportBatchModel",
    "SessionImportRowModel",
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
