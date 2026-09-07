from dataclasses import dataclass
from datetime import date

from app.domain.enums import (
    AccreditationStatus,
    PanelStatus,
    ProviderGender,
    ProviderTier,
    RelationType,
    StaffRole,
    UgandaRegion,
    WorkStatus,
)
from app.domain.value_objects.ids import ClientId, PersonId, UserId
from app.shared.utils.datetime import utc_now


@dataclass(frozen=True)
class LicenseInfo:
    number: str
    issuing_authority: str
    expiry_date: date | None = None

    def __post_init__(self):
        if not self.number or not self.issuing_authority:
            raise ValueError("License number and authority required")

    def is_valid(self) -> bool:
        if not self.expiry_date:
            return True
        return self.expiry_date >= utc_now().date()


@dataclass(frozen=True)
class ProviderProfile:
    """Panel-level metadata about a service provider (Joseph's framework).

    `tier` and `region` are None until a person assesses the practitioner;
    imported records arrive without either and are not bookable.
    """

    tier: ProviderTier | None
    region: UgandaRegion | None
    accreditation_status: AccreditationStatus
    panel_status: PanelStatus = PanelStatus.PENDING
    accreditation_authority: str | None = None
    accreditation_expiry: date | None = None
    specialties: tuple[str, ...] = ()
    bio: str | None = None
    gender: ProviderGender | None = None


@dataclass(frozen=True)
class ClientEmployeeCode:
    client_code: str
    family_code: str
    member_code: str

    def __post_init__(self):
        if not self.client_code or len(self.client_code) < 3 or len(self.client_code) > 5:
            raise ValueError("Client code must be 3-5 characters")
        if not self.family_code or len(self.family_code) != 2:
            raise ValueError("Family code must be 2 digits")
        if not self.member_code or len(self.member_code) != 2:
            raise ValueError("Member code must be 2 digits")
        if not self.family_code.isdigit():
            raise ValueError("Family code must be numeric")
        if not self.member_code.isdigit():
            raise ValueError("Member code must be numeric")

    def __str__(self) -> str:
        return f"{self.client_code}-{self.family_code}-{self.member_code}"

    @classmethod
    def from_string(cls, code_str: str) -> "ClientEmployeeCode":
        parts = code_str.split("-")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid code format: {code_str}. Expected format: CLIENT-FAMILY-MEMBER"
            )
        return cls(client_code=parts[0], family_code=parts[1], member_code=parts[2])


@dataclass(frozen=True)
class EmploymentInfo:
    client_id: ClientId
    employee_code: ClientEmployeeCode
    role: str
    start_date: date
    status: WorkStatus
    department: str | None = None
    employee_id: str | None = None
    end_date: date | None = None

    def __post_init__(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date must be after start date")

    def is_active(self) -> bool:
        return self.status == WorkStatus.ACTIVE


@dataclass(frozen=True)
class StaffInfo:
    role: StaffRole
    client_id: ClientId
    department: str | None = None
    can_manage_clients: bool = False
    can_manage_services: bool = False
    can_view_reports: bool = False


@dataclass(frozen=True)
class DependentInfo:
    primary_employee_id: PersonId
    relationship: RelationType
    guardian_id: UserId | None = None

    def __post_init__(self):
        if not self.primary_employee_id:
            raise ValueError("DependentInfo requires primary_employee_id")

    def is_eligible(self) -> bool:
        """Intrinsic eligibility derived from the dependent's own data.

        Cross-aggregate eligibility (the primary employee's active status)
        is composed at PersonEntity.is_eligible_for_services. Here we check
        only what this VO can know: the relationship type is one we accept,
        and the linkage to a primary employee is present.
        """
        return self.relationship in {
            RelationType.SPOUSE,
            RelationType.CHILD,
            RelationType.PARENT,
            RelationType.SIBLING,
            RelationType.GRANDPARENT,
            RelationType.GUARDIAN,
        }
