from enum import Enum


class ManagerConsultTopic(str, Enum):
    PERFORMANCE_CONCERN = "PerformanceConcern"
    DISCLOSURE_OF_SUICIDALITY = "DisclosureOfSuicidality"
    ACCOMMODATION = "Accommodation"
    TEAM_TRAUMA = "TeamTrauma"
    DISCIPLINE_VS_EAP = "DisciplineVsEAP"
    SUBSTANCE_USE = "SubstanceUse"
    DOMESTIC_VIOLENCE = "DomesticViolence"
    OTHER = "Other"


class WorkLifeServiceType(str, Enum):
    CHILDCARE = "Childcare"
    ELDERCARE = "Eldercare"
    LEGAL = "Legal"
    FINANCIAL = "Financial"
    IDENTITY_THEFT = "IdentityTheft"
    RELOCATION = "Relocation"
    PET_CARE = "PetCare"
    ADOPTION = "Adoption"
    DAILY_LIVING = "DailyLiving"


class WorkLifeReferralOutcome(str, Enum):
    REQUESTED = "Requested"
    ACCEPTED = "Accepted"
    DECLINED = "Declined"
    COMPLETED = "Completed"
    NO_SHOW = "NoShow"


class TrainingEnrolmentStatus(str, Enum):
    ENROLLED = "Enrolled"
    COMPLETED = "Completed"
    EXPIRED = "Expired"
    REVOKED = "Revoked"


class FitnessForDutyOutcome(str, Enum):
    """Non-clinical fit-for-duty result returned to the employer."""

    FIT = "Fit"
    FIT_WITH_RESTRICTIONS = "FitWithRestrictions"
    NOT_FIT = "NotFit"
    PENDING = "Pending"


class ReturnToWorkPlanStatus(str, Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
