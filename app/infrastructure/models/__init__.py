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
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.infrastructure.models.contact_model import ContactModel
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.document_model import DocumentModel
from app.infrastructure.models.industry_model import IndustryModel
from app.infrastructure.models.json_schemas import (
    DependentInfoDict,
    EmergencyContactDict,
    EmploymentInfoDict,
    LicenseInfoDict,
    StaffInfoDict,
)
from app.infrastructure.models.kpi_model import KPIAssignmentModel, KPIModel
from app.infrastructure.models.person_model import PersonModel
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.models.user_model import UserModel

__all__ = [
    "ActivityModel",
    "AuditLogModel",
    "Base",
    "ClientModel",
    "ClientTagModel",
    "ContactModel",
    "ContractModel",
    "CuidMixin",
    "DependentInfoDict",
    "DocumentModel",
    "EmergencyContactDict",
    "EmploymentInfoDict",
    "EntityChangeModel",
    "EnumValueType",
    "IndustryModel",
    "KPIAssignmentModel",
    "KPIModel",
    "LicenseInfoDict",
    "PersonModel",
    "ServiceAssignmentModel",
    "ServiceModel",
    "ServiceSessionModel",
    "SoftDeleteMixin",
    "StaffInfoDict",
    "TenantModel",
    "TenantMixin",
    "TimestampMixin",
    "UserModel",
]
