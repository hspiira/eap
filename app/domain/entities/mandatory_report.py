"""Mandatory-report aggregate.

Records a jurisdictional disclosure made when a ``RiskAssessment`` flags
``requires_mandatory_report``. Immutable once submitted; the only post-submission
operation is recording the external reference number returned by the receiving
authority. Never carries clinical detail in plaintext — the receiver/agency/
reference triple is what audit needs.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import MandatoryReportType
from app.domain.events import DomainEvent, MandatoryReportSubmitted
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    MandatoryReportId,
    RiskAssessmentId,
    TenantId,
    UserId,
)


@dataclass(frozen=True)
class MandatoryReport:
    id: MandatoryReportId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    risk_assessment_id: RiskAssessmentId
    report_type: MandatoryReportType
    submitted_to: str
    submitted_at: datetime
    submitted_by: UserId
    created_at: datetime
    case_id: CaseId | None = None
    crisis_contact_id: CrisisContactId | None = None
    external_reference_number: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.submitted_to:
            raise DomainError("submitted_to is required")
        if not self.events:
            object.__setattr__(
                self,
                "events",
                [
                    MandatoryReportSubmitted(
                        occurred_at=self.submitted_at,
                        mandatory_report_id=self.id,
                        report_type=self.report_type.value,
                        submitted_to=self.submitted_to,
                    )
                ],
            )
