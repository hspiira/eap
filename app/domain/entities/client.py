"""
Client Entity (Aggregate Root)

Represents an organizational client receiving EAP services.
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.domain.value_objects.core import ClientId, TenantId, UserId, ContactInfo, Address, IndustryId
from app.domain.enums import BaseStatus, ContactMethod
from app.domain.events import DomainEvent, ClientVerified, ClientActivated, ClientSuspended, ClientTerminated
from app.domain.exceptions import DomainError
from app.shared.utils.datetime import utc_now

@dataclass
class ClientEntity:
    # Required fields (no defaults)
    _id: ClientId
    _tenant_id: TenantId
    _name: str
    _contact_info: ContactInfo
    _status: BaseStatus
    _is_verified: bool
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields (with defaults)
    _billing_address: Address | None = None
    _industry_id: IndustryId | None = None
    _parent_client_id: ClientId | None = None
    _preferred_contact_method: ContactMethod | None = None
    _deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    
    def verify(self, verified_by: UserId) -> None:
        self._is_verified = True
        self._updated_at = utc_now()
        self._events.append(ClientVerified(occurred_at=utc_now(), client_id=self._id, verified_by=verified_by))
    
    def activate(self) -> None:
        """Activate client for operation"""
        if not self._contact_info.has_any_contact():
            raise DomainError("Active clients must have contact info")
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot activate deleted client")
        if self._status == BaseStatus.ACTIVE:
            raise DomainError("Client is already active")
        self._status = BaseStatus.ACTIVE
        self._updated_at = utc_now()
        self._events.append(ClientActivated(occurred_at=utc_now(), client_id=self._id))
    
    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate client"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot deactivate deleted client")
        if self._status == BaseStatus.INACTIVE:
            raise DomainError("Client is already inactive")
        self._status = BaseStatus.INACTIVE
        self._updated_at = utc_now()
    
    def suspend(self, reason: str) -> None:
        """Suspend client (e.g., payment issues)"""
        if not reason:
            raise DomainError("Suspension requires reason")
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot suspend deleted client")
        if self._status == BaseStatus.INACTIVE:
            raise DomainError("Client is already inactive")
        self._status = BaseStatus.INACTIVE
        self._updated_at = utc_now()
        self._events.append(ClientSuspended(occurred_at=utc_now(), client_id=self._id, reason=reason))
    
    def terminate(self, reason: str) -> None:
        """Permanently terminate client"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self._status == BaseStatus.DELETED:
            raise DomainError("Client is already terminated")
        self._status = BaseStatus.DELETED
        self._deleted_at = utc_now()
        self._updated_at = utc_now()
        self._events.append(ClientTerminated(occurred_at=utc_now(), client_id=self._id, reason=reason))
    
    def archive(self) -> None:
        """Archive client (softer than terminate)"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot archive deleted client")
        if self._status == BaseStatus.ARCHIVED:
            raise DomainError("Client is already archived")
        self._status = BaseStatus.ARCHIVED
        self._updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore archived or soft-deleted client"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot restore deleted client")
        # Check if client is already active and not deleted
        if self._status == BaseStatus.ACTIVE and self._deleted_at is None:
            raise DomainError("Client is already active and does not need restoration")
        # Restore soft-deleted client
        if self._deleted_at:
            self._deleted_at = None
        # Restore archived client
        if self._status == BaseStatus.ARCHIVED:
            self._status = BaseStatus.ACTIVE
        self._updated_at = utc_now()
    
    def update_name(self, name: str) -> None:
        """Update client name"""
        if not name:
            raise DomainError("Client name cannot be empty")
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update name for deleted client")
        self._name = name
        self._updated_at = utc_now()
    
    def update_contact_info(self, contact_info: ContactInfo) -> None:
        """Update contact information"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update contact info for deleted client")
        self._contact_info = contact_info
        self._updated_at = utc_now()
    
    def update_billing_address(self, address: Address | None) -> None:
        """Update billing address"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update billing address for deleted client")
        self._billing_address = address
        self._updated_at = utc_now()
    
    def update_preferred_contact_method(self, method: ContactMethod | None) -> None:
        """Update preferred contact method"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update preferred contact method for deleted client")
        self._preferred_contact_method = method
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if client is operational"""
        return self._status == BaseStatus.ACTIVE and self._deleted_at is None