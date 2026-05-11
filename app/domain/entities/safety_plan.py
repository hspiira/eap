"""Stanley-Brown safety plan aggregate.

Versioned, never edit-in-place. FSM ``Draft → Active → Reviewed → Superseded``.
Edits after activation are made by ``supersede_with(new_plan_id)`` so the prior
plan's content stays exactly as it was at the time it was active — important
for clinical defensibility.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import SafetyPlanStatus
from app.domain.events import (
    DomainEvent,
    SafetyPlanActivated,
    SafetyPlanCreated,
    SafetyPlanReviewed,
    SafetyPlanSuperseded,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    SafetyPlanId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class SafetyPlan:
    id: SafetyPlanId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    clinician_id: UserId
    status: SafetyPlanStatus
    warning_signs: tuple[str, ...]
    internal_coping_strategies: tuple[str, ...]
    social_distractions: tuple[str, ...]
    social_contacts_for_help: tuple[dict, ...]
    professional_help_resources: tuple[dict, ...]
    means_restriction_plan: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    case_id: CaseId | None = None
    crisis_contact_id: CrisisContactId | None = None
    activated_at: datetime | None = None
    next_review_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by: UserId | None = None
    supersedes_safety_plan_id: SafetyPlanId | None = None
    superseded_by: SafetyPlanId | None = None
    superseded_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        for name, value in {
            "warning_signs": self.warning_signs,
            "internal_coping_strategies": self.internal_coping_strategies,
            "social_distractions": self.social_distractions,
            "social_contacts_for_help": self.social_contacts_for_help,
            "professional_help_resources": self.professional_help_resources,
            "means_restriction_plan": self.means_restriction_plan,
        }.items():
            if not value:
                raise DomainError(f"safety plan requires {name}")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                SafetyPlanCreated(
                    occurred_at=self.created_at,
                    safety_plan_id=self.id,
                    clinical_subject_id=self.clinical_subject_id,
                )
            )

    def activate(self, *, now: datetime | None = None) -> None:
        if self.status != SafetyPlanStatus.DRAFT:
            raise InvalidStateError(
                f"Cannot activate a {self.status.value} safety plan"
            )
        now = now or utc_now()
        self.status = SafetyPlanStatus.ACTIVE
        self.activated_at = now
        self.updated_at = now
        self.events.append(
            SafetyPlanActivated(occurred_at=now, safety_plan_id=self.id)
        )

    def mark_reviewed(
        self, *, reviewer_id: UserId, now: datetime | None = None
    ) -> None:
        if self.status not in {
            SafetyPlanStatus.ACTIVE,
            SafetyPlanStatus.REVIEWED,
        }:
            raise InvalidStateError(
                f"Cannot review a {self.status.value} safety plan"
            )
        now = now or utc_now()
        self.status = SafetyPlanStatus.REVIEWED
        self.reviewed_at = now
        self.reviewed_by = reviewer_id
        self.updated_at = now
        self.events.append(
            SafetyPlanReviewed(
                occurred_at=now,
                safety_plan_id=self.id,
                reviewer_id=reviewer_id,
            )
        )

    def supersede_with(
        self,
        successor_id: SafetyPlanId,
        *,
        now: datetime | None = None,
    ) -> None:
        if self.status == SafetyPlanStatus.SUPERSEDED:
            raise InvalidStateError("Safety plan already superseded")
        if self.status == SafetyPlanStatus.DRAFT:
            raise InvalidStateError("Draft plans should be edited, not superseded")
        if successor_id == self.id:
            raise DomainError("A safety plan cannot supersede itself")
        now = now or utc_now()
        self.status = SafetyPlanStatus.SUPERSEDED
        self.superseded_at = now
        self.superseded_by = successor_id
        self.updated_at = now
        self.events.append(
            SafetyPlanSuperseded(
                occurred_at=now,
                superseded_safety_plan_id=self.id,
                successor_safety_plan_id=successor_id,
            )
        )
