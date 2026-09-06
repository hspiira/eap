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


class AliasResolutionState(str, Enum):
    """Whether a source name has been reconciled to a practitioner.

    `AMBIGUOUS` and `UNMAPPED` are distinct review outcomes: the first has
    candidates and no decision, the second has no candidate at all.
    """

    UNMAPPED = "Unmapped"
    AMBIGUOUS = "Ambiguous"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"


class ImportRowOutcome(str, Enum):
    """Per-row result of a staged historical import."""

    ACCEPTED = "Accepted"
    DUPLICATE = "Duplicate"
    CONFLICTING = "Conflicting"
    MISSING_PRACTITIONER = "MissingPractitioner"
    UNMAPPED_PRACTITIONER = "UnmappedPractitioner"
    AMBIGUOUS_PRACTITIONER = "AmbiguousPractitioner"
    REJECTED = "Rejected"


class ImportBatchStatus(str, Enum):
    """Lifecycle of a staged import batch."""

    STAGED = "Staged"
    APPLIED = "Applied"
    ABANDONED = "Abandoned"
