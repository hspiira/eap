"""One engagement-document checklist entry for a practitioner.

The source workbook tracks seven documents per provider with a state and an
occasional validity remark. Each entry is keyed by (tenant, provider, kind).
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import EngagementDocumentKind, EngagementDocumentState
from app.domain.events import DomainEvent
from app.domain.events.provider import ProviderEngagementDocumentRecorded
from app.domain.value_objects.ids import ProviderEngagementDocumentId, ProviderId, TenantId, UserId
from app.shared.utils.datetime import utc_now


@dataclass
class ProviderEngagementDocument:
    id: ProviderEngagementDocumentId
    tenant_id: TenantId
    provider_id: ProviderId
    document_kind: EngagementDocumentKind
    state: EngagementDocumentState
    note: str | None
    created_at: datetime
    updated_at: datetime
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def record_created(self, actor: UserId) -> None:
        """Emit the audit event for a newly written checklist entry."""
        self.events.append(self._recorded_event(actor, old_state=None))

    def update_record(
        self, state: EngagementDocumentState, note: str | None, actor: UserId
    ) -> None:
        """Change state or note. A no-op update emits nothing."""
        if self.state == state and self.note == note:
            return
        previous = self.state
        self.state = state
        self.note = note
        self.updated_at = utc_now()
        self.events.append(self._recorded_event(actor, old_state=previous.value))

    def _recorded_event(
        self, actor: UserId, *, old_state: str | None
    ) -> ProviderEngagementDocumentRecorded:
        return ProviderEngagementDocumentRecorded(
            occurred_at=utc_now(),
            provider_id=self.provider_id,
            document_kind=self.document_kind.value,
            old_state=old_state,
            new_state=self.state.value,
            note=self.note,
            actor=actor,
        )
