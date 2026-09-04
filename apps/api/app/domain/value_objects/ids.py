"""Identifier value objects.

Each entity has its own ID subclass so the type checker can flag
cross-type misuse (e.g. passing a PersonId where a UserId is expected).
Runtime behaviour is identical to the base ``Id``: same string validation,
same equality semantics. Subclasses exist purely for nominal typing.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Id:
    """Base identifier value object.

    Attributes:
    - 1..25 characters
    - immutable
    """

    value: str

    def __post_init__(self):
        if not self.value or len(self.value) > 25:
            raise ValueError("ID must be 1..25 characters")


@dataclass(frozen=True)
class TenantId(Id):
    pass


@dataclass(frozen=True)
class PersonId(Id):
    pass


@dataclass(frozen=True)
class ContractId(Id):
    pass


@dataclass(frozen=True)
class ServiceId(Id):
    pass


@dataclass(frozen=True)
class SessionId(Id):
    pass


@dataclass(frozen=True)
class UserId(Id):
    pass


@dataclass(frozen=True)
class ClientId(Id):
    pass


@dataclass(frozen=True)
class ClientAliasId(Id):
    pass


@dataclass(frozen=True)
class IndustryId(Id):
    pass


@dataclass(frozen=True)
class AuditLogId(Id):
    pass


@dataclass(frozen=True)
class EntityChangeId(Id):
    pass


@dataclass(frozen=True)
class DocumentId(Id):
    pass


@dataclass(frozen=True)
class KPIId(Id):
    pass


@dataclass(frozen=True)
class KPIAssignmentId(Id):
    pass


@dataclass(frozen=True)
class ClientTagId(Id):
    pass


@dataclass(frozen=True)
class ContactId(Id):
    pass


@dataclass(frozen=True)
class ActivityId(Id):
    pass


@dataclass(frozen=True)
class ServiceAssignmentId(Id):
    pass


@dataclass(frozen=True)
class CriticalIncidentId(Id):
    pass


@dataclass(frozen=True)
class NonCompeteClauseId(Id):
    pass


@dataclass(frozen=True)
class ReportTemplateId(Id):
    pass


@dataclass(frozen=True)
class ReportRunId(Id):
    pass


@dataclass(frozen=True)
class UtilisationEventId(Id):
    pass


@dataclass(frozen=True)
class CareCallbackCampaignId(Id):
    pass


@dataclass(frozen=True)
class OutreachRecordId(Id):
    pass


@dataclass(frozen=True)
class TriageResponseId(Id):
    pass


@dataclass(frozen=True)
class SurveyCampaignId(Id):
    pass


@dataclass(frozen=True)
class SurveyResponseId(Id):
    pass


@dataclass(frozen=True)
class EngagementId(Id):
    pass


@dataclass(frozen=True)
class DeliverableId(Id):
    pass


@dataclass(frozen=True)
class HoursLogEntryId(Id):
    pass


@dataclass(frozen=True)
class DSARRequestId(Id):
    pass


@dataclass(frozen=True)
class BenchmarkConsentId(Id):
    pass


@dataclass(frozen=True)
class EligibleMemberId(Id):
    pass


@dataclass(frozen=True)
class ClinicalSubjectId(Id):
    pass


@dataclass(frozen=True)
class CaseId(Id):
    pass


@dataclass(frozen=True)
class AuthorizationId(Id):
    pass


@dataclass(frozen=True)
class EAPProgrammeId(Id):
    pass


@dataclass(frozen=True)
class ClinicalNoteId(Id):
    pass


@dataclass(frozen=True)
class NoteAmendmentId(Id):
    pass


@dataclass(frozen=True)
class CrisisContactId(Id):
    pass


@dataclass(frozen=True)
class RiskAssessmentId(Id):
    pass


@dataclass(frozen=True)
class SafetyPlanId(Id):
    pass


@dataclass(frozen=True)
class MandatoryReportId(Id):
    pass


@dataclass(frozen=True)
class CaringContactId(Id):
    pass


@dataclass(frozen=True)
class ManagerConsultId(Id):
    pass


@dataclass(frozen=True)
class WorkLifeReferralId(Id):
    pass


@dataclass(frozen=True)
class WorkLifeProviderId(Id):
    pass


@dataclass(frozen=True)
class TrainingEnrolmentId(Id):
    pass


@dataclass(frozen=True)
class OutcomeMeasureId(Id):
    pass


@dataclass(frozen=True)
class FitnessForDutyId(Id):
    pass


@dataclass(frozen=True)
class ReturnToWorkPlanId(Id):
    pass


@dataclass(frozen=True)
class ConsentId(Id):
    pass


@dataclass(frozen=True)
class DataSharingRegisterEntryId(Id):
    pass


@dataclass(frozen=True)
class DPOContactId(Id):
    pass
