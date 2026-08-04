"""Risk assessment + safety plan + mandatory report + caring contact repository ports."""

from app.domain.entities.caring_contact import CaringContact
from app.domain.entities.mandatory_report import MandatoryReport
from app.domain.entities.risk_assessment import RiskAssessment
from app.domain.entities.safety_plan import SafetyPlan
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    CaringContactId,
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    MandatoryReportId,
    RiskAssessmentId,
    SafetyPlanId,
    TenantId,
)


class RiskAssessmentRepository(BaseRepository[RiskAssessment, RiskAssessmentId]):
    async def list_for_case(self, tenant_id: TenantId, case_id: CaseId) -> list[RiskAssessment]: ...

    async def list_for_crisis_contact(
        self, tenant_id: TenantId, crisis_contact_id: CrisisContactId
    ) -> list[RiskAssessment]: ...


class SafetyPlanRepository(BaseRepository[SafetyPlan, SafetyPlanId]):
    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[SafetyPlan]: ...


class MandatoryReportRepository(BaseRepository[MandatoryReport, MandatoryReportId]):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100
    ) -> list[MandatoryReport]: ...


class CaringContactRepository(BaseRepository[CaringContact, CaringContactId]):
    async def list_pending(
        self, tenant_id: TenantId, *, before: object | None = None
    ) -> list[CaringContact]: ...

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[CaringContact]: ...
