"""Provider organisation aggregate."""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.events import DomainEvent
from app.domain.events.provider_network import (
    ProviderOrganisationApprovalChanged,
    ProviderOrganisationCreated,
    ProviderOrganisationDeactivated,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import ProviderOrganisationId
from app.shared.utils.datetime import utc_now


@dataclass
class ProviderOrganisationEntity:
    """A firm a tenant contracts with, which practitioners may be affiliated to.

    `is_active` is the record's operational state; `approval_status` is the
    supplier's approval to deliver. Organisation delivery requires both.
    """

    id: ProviderOrganisationId
    tenant_id: TenantId
    name: str
    created_at: datetime
    updated_at: datetime
    registration_number: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_active: bool = True
    approval_status: OrganisationApprovalStatus = OrganisationApprovalStatus.PENDING
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainError("Provider organisation requires a name")

    def can_deliver(self) -> bool:
        return self.is_active and self.approval_status is OrganisationApprovalStatus.APPROVED

    def record_created(self, actor: UserId) -> None:
        self.events.append(
            ProviderOrganisationCreated(
                occurred_at=utc_now(),
                organisation_id=self.id,
                tenant_id=self.tenant_id,
                name=self.name,
                actor=actor,
            )
        )

    def change_approval(
        self, new_status: OrganisationApprovalStatus, actor: UserId, reason: str
    ) -> None:
        _require_reason(reason)
        if self.approval_status is new_status:
            return
        old = self.approval_status
        self.approval_status = new_status
        self.updated_at = utc_now()
        self.events.append(
            ProviderOrganisationApprovalChanged(
                occurred_at=self.updated_at,
                organisation_id=self.id,
                tenant_id=self.tenant_id,
                old_status=old.value,
                new_status=new_status.value,
                actor=actor,
                reason=reason,
            )
        )

    def deactivate(self, actor: UserId, reason: str) -> None:
        """Retire the organisation without deleting it.

        Affiliations and delivered sessions reference it, so decision 2 keeps
        the row and its history.
        """
        _require_reason(reason)
        if not self.is_active:
            return
        self.is_active = False
        self.updated_at = utc_now()
        self.events.append(
            ProviderOrganisationDeactivated(
                occurred_at=self.updated_at,
                organisation_id=self.id,
                tenant_id=self.tenant_id,
                actor=actor,
                reason=reason,
            )
        )

    def reactivate(self, actor: UserId, reason: str) -> None:
        _require_reason(reason)
        if self.is_active:
            return
        self.is_active = True
        self.updated_at = utc_now()
        self.events.append(
            ProviderOrganisationApprovalChanged(
                occurred_at=self.updated_at,
                organisation_id=self.id,
                tenant_id=self.tenant_id,
                old_status=self.approval_status.value,
                new_status=self.approval_status.value,
                actor=actor,
                reason=reason,
            )
        )

    def clear_events(self) -> None:
        self.events.clear()


def _require_reason(reason: str) -> None:
    if not reason or not reason.strip():
        raise DomainError("A reason is required for this change")
