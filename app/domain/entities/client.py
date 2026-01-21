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
    _id: ClientId
    _tenant_id: TenantId
    
    _name: str
    _contact_info: ContactInfo  # Value Object
    _billing_address: Address | None = None  # Value Object
    
    _industry_id: IndustryId | None = None
    _parent_client_id: ClientId | None = None
    
    _status: BaseStatus
    _is_verified: bool
    _preferred_contact_method: ContactMethod | None = None
    
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None = None
    
    _events: list[DomainEvent] = field(default_factory=list)
    
    def verify(self, verified_by: UserId) -> None:
        self._is_verified = True
        self._updated_at = utc_now()
        self._events.append(ClientVerified(occurred_at=utc_now(), client_id=self._id, verified_by=verified_by))
    
    def activate(self) -> None:
        if not self._contact_info.has_any_contact():
            raise DomainError("Active clients must have contact info")
        self._status = BaseStatus.ACTIVE
        self._updated_at = utc_now()
        self._events.append(ClientActivated(occurred_at=utc_now(), client_id=self._id))
    
    def is_active(self) -> bool:
        return self._status == BaseStatus.ACTIVE and self._deleted_at is None