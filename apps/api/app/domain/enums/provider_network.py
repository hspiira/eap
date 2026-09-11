"""Enums for the provider network: organisations, affiliations and imports."""

from enum import Enum


class OrganisationApprovalStatus(str, Enum):
    """Supplier approval to deliver, held separately from the record's state.

    Eligibility needs "not active" and "not approved" as distinct reasons, so a
    deactivated record and a suspended supplier do not collapse into one value.
    """

    PENDING = "Pending"
    APPROVED = "Approved"
    SUSPENDED = "Suspended"
    REVOKED = "Revoked"


class DeliveryContext(str, Enum):
    """How a session was delivered.

    `UNKNOWN` records missing historical evidence and is never a valid choice
    for a new booking.
    """

    DIRECT = "Direct"
    ORGANISATION = "Organisation"
    UNKNOWN = "Unknown"


class ImportRowOutcome(str, Enum):
    """Per-row result of a staged historical import."""

    ACCEPTED = "Accepted"
    DUPLICATE = "Duplicate"
    CONFLICTING = "Conflicting"
    MISSING_PRACTITIONER = "MissingPractitioner"
    UNMAPPED_PRACTITIONER = "UnmappedPractitioner"
    AMBIGUOUS_PRACTITIONER = "AmbiguousPractitioner"
    UNRESOLVED_CLIENT = "UnresolvedClient"
    UNRESOLVED_MEMBER = "UnresolvedMember"
    UNRESOLVED_SERVICE = "UnresolvedService"
    REJECTED = "Rejected"
    #: An Accepted row the historical write path refused at apply time (a
    #: race with reference data, a constraint the writer enforces). Distinct
    #: from every outcome above, which staging alone can reach.
    FAILED = "Failed"


class ImportBatchStatus(str, Enum):
    """Lifecycle of a staged import batch."""

    STAGED = "Staged"
    APPLIED = "Applied"
    ABANDONED = "Abandoned"


class PractitionerImportOutcome(str, Enum):
    """Per-row result of a staged practitioner workbook import.

    Not ImportRowOutcome: those values name session-extract resolutions
    (member, service, practitioner lookup) that do not exist here, and none
    of them means "a person must decide before this row can be applied".
    """

    ACCEPTED = "Accepted"
    NEEDS_REVIEW = "NeedsReview"
    DUPLICATE = "Duplicate"
    REJECTED = "Rejected"


class ImportReasonCode(str, Enum):
    """Machine-readable code for a staged row's outcome reason (P-10).

    A message alone is fine to display but not to build a review UI or any
    other consumer against: rewording it silently breaks a string match.
    Every reason attached to a row carries one of these alongside its
    human-readable message.
    """

    ALREADY_STAGED = "AlreadyStaged"
    MISSING_NAME = "MissingName"
    UNMAPPED_PROFESSION = "UnmappedProfession"
    UNMAPPED_SPECIALITY = "UnmappedSpeciality"
    DUPLICATE_NAME_CANDIDATE = "DuplicateNameCandidate"
    ORGANISATION_NAME_COLLISION = "OrganisationNameCollision"
    MULTI_EMAIL_CELL = "MultiEmailCell"
    EMPLOYEE_CONTRACT_MEMO = "EmployeeContractMemo"
    APPLY_FAILED = "ApplyFailed"
    # Rows staged before reasons carried codes hold bare strings; they read
    # back under this code rather than failing the whole listing.
    LEGACY = "Legacy"
