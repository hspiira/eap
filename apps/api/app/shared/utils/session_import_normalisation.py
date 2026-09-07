"""Version-controlled normalisation tables for the session import (S-06).

One explicit mapping per source column, applied at staging. A value with no
entry returns Unmapped; nothing here uses .title() or fuzzy matching. Lookup
keys are deterministic: strip, collapse internal whitespace, casefold. Every
entry was enumerated from the reference extract
(sha256 0e8fa212455ea42bba48574eb46c639ade1238bc9fa7382bfc7eee1951774e44).

CLIENT FEEDBACK deliberately has no table. It is free text with 56 spellings,
and PRIV-01 forbids free text reaching an employer aggregate. It is never
imported as a category.
"""

from dataclasses import dataclass

from app.domain.enums import (
    ClientType,
    MemberGender,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)


@dataclass(frozen=True)
class Unmapped:
    """A non-blank source value with no entry in its column's table."""

    column: str
    value: str


@dataclass(frozen=True)
class StatusMapping:
    """A source status resolves to exactly one of two enums.

    No Show is a scheduling status, not a clinical outcome, so a mapped
    status carries either a clinical side or a scheduling side, never both.
    """

    clinical_status: SessionClinicalStatus | None = None
    session_status: SessionStatus | None = None


def _key(value: str) -> str:
    return " ".join(value.split()).casefold()


def _lookup[T](column: str, table: dict[str, T], raw: str | None) -> T | Unmapped | None:
    """Blank stays blank; an unlisted value is Unmapped, never defaulted."""
    if raw is None or not raw.strip():
        return None
    return table.get(_key(raw), Unmapped(column=column, value=raw.strip()))


_SESSION_TYPE: dict[str, SessionType] = {
    "physical": SessionType.PHYSICAL,
    "online": SessionType.ONLINE,
}

# 25 of the 50 distinct spellings map; the other 25 are topic, time or
# session-type bleed ("Depression", "10:00AM", "online") and stay unmapped.
_CATEGORY: dict[str, SessionCategory] = {
    "individual": SessionCategory.INDIVIDUAL,
    "individual conselling": SessionCategory.INDIVIDUAL,
    "individual counselling": SessionCategory.INDIVIDUAL,
    "individual counseling": SessionCategory.INDIVIDUAL,
    "indididual": SessionCategory.INDIVIDUAL,
    "individuual": SessionCategory.INDIVIDUAL,
    "group": SessionCategory.GROUP,
    "group session": SessionCategory.GROUP,
    "group conselling": SessionCategory.GROUP,
    "group presentation": SessionCategory.GROUP,
    "onsite group": SessionCategory.GROUP,
    "health talk": SessionCategory.GROUP,
    "family": SessionCategory.FAMILY,
    "family conselling": SessionCategory.FAMILY,
    "couple": SessionCategory.COUPLES,
    "couple conselling": SessionCategory.COUPLES,
    "couples counselling": SessionCategory.COUPLES,
}

_CLIENT_TYPE: dict[str, ClientType] = {
    "new": ClientType.NEW,
    "repeat": ClientType.REPEAT,
}

_STATUS: dict[str, StatusMapping] = {
    "ongoing": StatusMapping(clinical_status=SessionClinicalStatus.TO_BE_CONTINUED),
    "completed": StatusMapping(clinical_status=SessionClinicalStatus.COMPLETED),
    "referred": StatusMapping(clinical_status=SessionClinicalStatus.REFERRED),
    "terminated": StatusMapping(clinical_status=SessionClinicalStatus.TERMINATED),
    "no show": StatusMapping(session_status=SessionStatus.NO_SHOW),
}

# Group is not a gender. On 642 rows it signals a company-wide session, so
# the classifier returns the attendance and the member gender is absent.
_GENDER: dict[str, MemberGender | SessionAttendance] = {
    "female": MemberGender.FEMALE,
    "male": MemberGender.MALE,
    "group": SessionAttendance.COMPANY_WIDE,
}

# Blocked on a clinician (SESSIONS_IMPLEMENTATION.md B2). These tables stay
# empty until the controlled clinical list exists; every value stages as
# Unmapped. Do not populate them from engineering.
_DIAGNOSIS_TYPE: dict[str, str] = {}
_DIAGNOSIS: dict[str, str] = {}
_CLASSIFICATION: dict[str, str] = {}


def map_session_type(raw: str | None) -> SessionType | Unmapped | None:
    """Map a SESSION TYPE value."""
    return _lookup("SESSION TYPE", _SESSION_TYPE, raw)


def map_category(raw: str | None) -> SessionCategory | Unmapped | None:
    """Map a CATEGORY value."""
    return _lookup("CATEGORY", _CATEGORY, raw)


def map_client_type(raw: str | None) -> ClientType | Unmapped | None:
    """Map a CLIENT TYPE value."""
    return _lookup("CLIENT TYPE", _CLIENT_TYPE, raw)


def map_status(raw: str | None) -> StatusMapping | Unmapped | None:
    """Map a STATUS (CLEAN) value onto the two enums it spans.

    The 811 blank rows return None and must not get a default.
    """
    return _lookup("STATUS (CLEAN)", _STATUS, raw)


def classify_gender(raw: str | None) -> MemberGender | SessionAttendance | Unmapped | None:
    """Classify a GENDER value: a member gender or the company-wide signal."""
    return _lookup("GENDER", _GENDER, raw)


def map_diagnosis_type(raw: str | None) -> str | Unmapped | None:
    """Map a DIAGNOSIS TYPE value; the table is empty pending a clinician."""
    return _lookup("DIAGNOSIS TYPE", _DIAGNOSIS_TYPE, raw)


def map_diagnosis(raw: str | None) -> str | Unmapped | None:
    """Map a DIAGNOSIS value; the table is empty pending a clinician."""
    return _lookup("DIAGNOSIS", _DIAGNOSIS, raw)


def map_classification(raw: str | None) -> str | Unmapped | None:
    """Map a CLASSIFICATION value; the table is empty pending a clinician."""
    return _lookup("CLASSIFICATION", _CLASSIFICATION, raw)
