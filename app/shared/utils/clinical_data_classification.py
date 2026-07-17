"""Classifier identifying which audit events touch special-category clinical data.

The DPO uses this classification to produce a separate "special-category data
accessed" report alongside the regular audit stream. The default rule is
"opt-in by resource type / event name" — anything not on the explicit list is
treated as ordinary so the flag never silently drifts.

To classify a new clinical aggregate, add its `resource_type` string to
``CLINICAL_RESOURCE_TYPES`` or the matching event-type pattern to
``CLINICAL_EVENT_PATTERNS``.
"""

from __future__ import annotations

CLINICAL_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "ClinicalSubject",
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


def is_clinical_resource(resource_type: str | None) -> bool:
    if not resource_type:
        return False
    return resource_type in CLINICAL_RESOURCE_TYPES


def is_clinical_event(event_type: str | None) -> bool:
    if not event_type:
        return False
    return any(p in event_type for p in CLINICAL_EVENT_PATTERNS)


def is_special_category(
    *, resource_type: str | None = None, event_type: str | None = None
) -> bool:
    """True when either the resource type or event name flags clinical data."""
    return is_clinical_resource(resource_type) or is_clinical_event(event_type)
