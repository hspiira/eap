"""Classifier identifying which audit events touch special-category clinical data.

The DPO uses this classification to produce a separate "special-category data
accessed" report alongside the regular audit stream. The default rule is
"opt-in by resource type / event name"; anything not on the explicit list is
treated as ordinary so the flag never silently drifts.

To classify a new clinical aggregate, add its `resource_type` string to
``CLINICAL_RESOURCE_TYPES`` or the matching event-type pattern to
``CLINICAL_EVENT_PATTERNS``.
"""

from __future__ import annotations

CLINICAL_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "ClinicalSubject",
        "ServiceSession",
        "Case",
        "ClinicalNote",
        "RiskAssessment",
        "SafetyPlan",
        "MandatoryReport",
        "CrisisContact",
        "OutreachRecord",
        "ManagerConsult",
        "WorkLifeReferral",
        "OutcomeMeasure",
        "FitnessForDuty",
        "ReturnToWorkPlan",
    }
)


CLINICAL_EVENT_PATTERNS: tuple[str, ...] = (
    "Triage",
    "Crisis",
    "RiskAssessment",
    "SafetyPlan",
    "Clinical",
    "MandatoryReport",
    "OutcomeMeasure",
)


# Personal data the DPO reports on alongside the clinical set. A roster row is
# not clinical, and whether it belongs under "special category" at all is the
# DPO's call: the flag is preserved here because members carried it before the
# audit paths converged, not because this file decided it.
SPECIAL_CATEGORY_RESOURCE_TYPES: frozenset[str] = CLINICAL_RESOURCE_TYPES | frozenset(
    {"EligibleMember", "MemberNextOfKin"}
)


# A next of kin never consented to being on the system: they are named by
# somebody else. A member's row carries government identifiers, a date of birth
# and contact details, which are no less sensitive, so neither records field
# values in the diff. The audit store is append-only and outside the reach of a
# rectification or erasure request, so a value written here is a permanent copy
# that the data subject cannot correct or remove. The field name and the fact of
# the change are the auditable facts; the values live on the record itself,
# where they can still be changed.
REDACTED_RESOURCE_TYPES: frozenset[str] = CLINICAL_RESOURCE_TYPES | frozenset(
    {"EligibleMember", "MemberNextOfKin"}
)


def redacts_content(resource_type: str | None) -> bool:
    """Whether a field diff on this resource must drop its values.

    Redaction follows content, not the reporting flag. What changed and who
    changed it is still recorded for every resource; only the before and after
    values are dropped, and only where the record holds data a permanent copy
    would outlive the subject's right to correct it.
    """
    return bool(resource_type) and resource_type in REDACTED_RESOURCE_TYPES


def is_clinical_resource(resource_type: str | None) -> bool:
    if not resource_type:
        return False
    return resource_type in CLINICAL_RESOURCE_TYPES


def is_clinical_event(event_type: str | None) -> bool:
    if not event_type:
        return False
    return any(p in event_type for p in CLINICAL_EVENT_PATTERNS)


def is_special_category(*, resource_type: str | None = None, event_type: str | None = None) -> bool:
    """True when either the resource type or event name flags reportable data."""
    reportable = bool(resource_type) and resource_type in SPECIAL_CATEGORY_RESOURCE_TYPES
    return reportable or is_clinical_event(event_type)
