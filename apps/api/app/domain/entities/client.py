"""
Client Entity (Aggregate Root)

Represents an organizational client receiving EAP services.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import BaseStatus, ClientTier, ContactMethod
from app.domain.events import (
    ClientActivated,
    ClientDeactivated,
    ClientSuspended,
    ClientTerminated,
    ClientVerified,
    DomainEvent,
)
from app.domain.exceptions import ConflictError, DomainError
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    IndustryId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class ClientEntity:
    # Required fields (no defaults)
    id: ClientId
    tenant_id: TenantId
    name: str
    code: str  # 3-5 character unique code per tenant (e.g., "MNT")
    contact_info: ContactInfo
    status: BaseStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    # Optional fields (with defaults)
    billing_address: Address | None = None
    industry_id: IndustryId | None = None
    parent_client_id: ClientId | None = None
    preferred_contact_method: ContactMethod | None = None
    tier: ClientTier | None = None
    suspension_reason: str | None = None
    aliases: list[str] = field(default_factory=list[str])
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def verify(self, verified_by: UserId) -> None:
        self.is_verified = True
        self.updated_at = utc_now()
        self.events.append(
            ClientVerified(occurred_at=utc_now(), client_id=self.id, verified_by=verified_by)
        )

    def activate(self) -> None:
        """Activate client for operation"""
        if not self.contact_info.has_any_contact():
            raise DomainError("Active clients must have contact info")
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot activate deleted client")
        if self.status == BaseStatus.ACTIVE:
            raise ConflictError("Client is already active")
        self.status = BaseStatus.ACTIVE
        self.suspension_reason = None
        self.updated_at = utc_now()
        self.events.append(ClientActivated(occurred_at=utc_now(), client_id=self.id))

    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate client"""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot deactivate deleted client")
        if self.status == BaseStatus.INACTIVE:
            raise ConflictError("Client is already inactive")
        self.status = BaseStatus.INACTIVE
        self.suspension_reason = None
        self.updated_at = utc_now()
        self.events.append(
            ClientDeactivated(
                occurred_at=utc_now(), client_id=self.id, reason=reason or "Deactivated"
            )
        )

    def suspend(self, reason: str) -> None:
        """Suspend client (e.g., payment issues)"""
        if not reason:
            raise DomainError("Suspension requires reason")
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot suspend deleted client")
        if self.status == BaseStatus.INACTIVE:
            raise ConflictError("Client is already inactive")
        self.status = BaseStatus.INACTIVE
        self.suspension_reason = reason.strip()
        self.updated_at = utc_now()
        self.events.append(ClientSuspended(occurred_at=utc_now(), client_id=self.id, reason=reason))

    def terminate(self, reason: str) -> None:
        """Permanently terminate client"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self.status == BaseStatus.DELETED:
            raise ConflictError("Client is already terminated")
        self.status = BaseStatus.DELETED
        self.deleted_at = utc_now()
        self.updated_at = utc_now()
        self.events.append(
            ClientTerminated(occurred_at=utc_now(), client_id=self.id, reason=reason)
        )

    def archive(self) -> None:
        """Archive client (softer than terminate)"""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot archive deleted client")
        if self.status == BaseStatus.ARCHIVED:
            raise ConflictError("Client is already archived")
        self.status = BaseStatus.ARCHIVED
        self.updated_at = utc_now()

    def restore(self) -> None:
        """Restore an archived client to active operation."""
        if self.status != BaseStatus.ARCHIVED:
            raise DomainError("Only archived clients can be restored")
        self.status = BaseStatus.ACTIVE
        self.suspension_reason = None
        self.updated_at = utc_now()

    def update_name(self, name: str) -> None:
        """Update client name"""
        if not name:
            raise DomainError("Client name cannot be empty")
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update name for deleted client")
        self.name = name
        self.updated_at = utc_now()

    def update_contact_info(self, contact_info: ContactInfo) -> None:
        """Update contact information"""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update contact info for deleted client")
        self.contact_info = contact_info
        self.updated_at = utc_now()

    def update_billing_address(self, billing_address: Address | None) -> None:
        """Update billing address"""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update billing address for deleted client")
        self.billing_address = billing_address
        self.updated_at = utc_now()

    def update_industry(self, industry_id: IndustryId | None) -> None:
        """Update or clear the client's industry classification."""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update industry for deleted client")
        self.industry_id = industry_id
        self.updated_at = utc_now()

    def update_preferred_contact_method(self, method: ContactMethod | None) -> None:
        """Update preferred contact method"""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update preferred contact method for deleted client")
        self.preferred_contact_method = method
        self.updated_at = utc_now()

    def update_tier(self, tier: ClientTier | None) -> None:
        """Set the engagement tier (A/B/C) used by reporting and pricing."""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update tier for deleted client")
        self.tier = tier
        self.updated_at = utc_now()

    def is_active(self) -> bool:
        """Check if client is operational"""
        return self.status == BaseStatus.ACTIVE and self.deleted_at is None

    # === Public Properties ===

    def clear_events(self) -> None:
        """Clear collected domain events after publishing."""
        self.events.clear()
