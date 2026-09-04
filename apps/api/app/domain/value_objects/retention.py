"""Per-data-class retention policy (Phase 4 #DSAR / SAD §6.6).

Declared in code rather than in a config table; these values change rarely and
need to be reviewed by legal whenever they do, so a code-review-gated constant
is the right surface for v1. A future iteration can promote this to a tenant
override table if multi-jurisdiction tenants need divergent windows.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import RetentionDataClass
from app.domain.exceptions import DomainError


@dataclass(frozen=True)
class RetentionPolicy:
    """How long one data class is kept after the subject leaves the system."""

    data_class: RetentionDataClass
    days: int
    rationale: str

    def __post_init__(self) -> None:
        if self.days < 0:
            raise DomainError("Retention days cannot be negative")
        if not self.rationale:
            raise DomainError("Retention policy requires a rationale")


DEFAULT_RETENTION_POLICIES: tuple[RetentionPolicy, ...] = (
    RetentionPolicy(
        data_class=RetentionDataClass.SESSIONS,
        days=2555,  # 7 years
        rationale="Clinical record retention per Uganda Medical Council guidance",
    ),
    RetentionPolicy(
        data_class=RetentionDataClass.TRIAGE,
        days=2555,
        rationale="Triage responses are part of the clinical record",
    ),
    RetentionPolicy(
        data_class=RetentionDataClass.SURVEY,
        days=730,  # 2 years
        rationale="Anonymous survey aggregates retained for trend analysis",
    ),
    RetentionPolicy(
        data_class=RetentionDataClass.AUDIT,
        days=2555,
        rationale="Audit chain retention required for SOC 2 and DPDP compliance",
    ),
    RetentionPolicy(
        data_class=RetentionDataClass.ENGAGEMENTS,
        days=2555,
        rationale="Consultancy work-product retention per professional standards",
    ),
    RetentionPolicy(
        data_class=RetentionDataClass.OUTREACH,
        days=2555,
        rationale="Care-callback outcomes are clinical records",
    ),
)


def policy_for(data_class: RetentionDataClass) -> RetentionPolicy:
    """Look up the active policy for a data class."""
    for p in DEFAULT_RETENTION_POLICIES:
        if p.data_class == data_class:
            return p
    raise DomainError(f"No retention policy defined for {data_class.value}")


ERASURE_REVERSIBLE_WINDOW_DAYS = 14
"""Subjects can cancel an erasure within this many days of submission."""
