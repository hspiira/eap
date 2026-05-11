"""Data-sharing register entry.

Records every actual PHI disclosure event so the DPO can produce a regulator-
ready ledger. Each entry references the governing ``Consent`` (or carries a
reason when the disclosure was statutory / consent-not-applicable), the
receiving party, what was shared, and when. Immutable post-creation.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import ConsentScope
from app.domain.events import DataShareLogged, DomainEvent
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    ConsentId,
    DataSharingRegisterEntryId,
    TenantId,
    UserId,
)


@dataclass(frozen=True)
class DataSharingRegisterEntry:
    id: DataSharingRegisterEntryId
    tenant_id: TenantId
    subject_clinical_subject_id: ClinicalSubjectId
    shared_with: str
    scope: ConsentScope
    summary_of_data_shared: str
    shared_at: datetime
    shared_by: UserId
    created_at: datetime
    consent_id: ConsentId | None = None
    legal_basis: str | None = None
    case_id: CaseId | None = None
    delivery_channel: str | None = None
    delivery_reference: str | None = None
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.shared_with:
            raise DomainError("shared_with is required")
        if not self.summary_of_data_shared:
            raise DomainError("summary_of_data_shared is required")
        if self.consent_id is None and not self.legal_basis:
            raise DomainError(
                "A data-sharing entry without a consent_id requires a "
                "legal_basis (e.g. statutory order, mandatory report)"
            )
        if not self.events:
            object.__setattr__(
                self,
                "events",
                [
                    DataShareLogged(
                        occurred_at=self.shared_at,
                        entry_id=self.id,
                        consent_id=self.consent_id,
                        shared_with=self.shared_with,
                        scope=self.scope.value,
                    )
                ],
            )
