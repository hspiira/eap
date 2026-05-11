"""Clinical subject aggregate.

The pseudonymous identity used by every clinical aggregate (Case, ClinicalNote,
RiskAssessment, SafetyPlan, CrisisContact). Carries no PII — name, email, and
employer-side identifiers are deliberately absent. The only way to resolve a
clinical subject back to an EligibleMember is via the audited
``eligible_member_clinical_link`` mapping.

Existence of this aggregate is the structural keystone of the privacy wall.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ClinicalSubjectId,
    TenantId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class ClinicalSubject:
    id: ClinicalSubjectId
    tenant_id: TenantId
    pseudonym: str
    created_at: datetime
    updated_at: datetime
    preferred_language: str | None = None
    preferred_pronouns: str | None = None
    preferred_contact_method: str | None = None
    notes_for_continuity: str | None = None
    is_active: bool = True
    deactivated_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.pseudonym:
            raise DomainError("ClinicalSubject requires a pseudonym")
        if len(self.pseudonym) < 8:
            raise DomainError("pseudonym must be at least 8 characters")

    def update_continuity_metadata(
        self,
        *,
        preferred_language: str | None = None,
        preferred_pronouns: str | None = None,
        preferred_contact_method: str | None = None,
        notes_for_continuity: str | None = None,
    ) -> None:
        if preferred_language is not None:
            self.preferred_language = preferred_language
        if preferred_pronouns is not None:
            self.preferred_pronouns = preferred_pronouns
        if preferred_contact_method is not None:
            self.preferred_contact_method = preferred_contact_method
        if notes_for_continuity is not None:
            self.notes_for_continuity = notes_for_continuity
        self.updated_at = utc_now()

    def deactivate(self, now: datetime | None = None) -> None:
        if not self.is_active:
            return
        now = now or utc_now()
        self.is_active = False
        self.deactivated_at = now
        self.updated_at = now
