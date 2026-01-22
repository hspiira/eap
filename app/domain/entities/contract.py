"""
Contract Entity

Represents a service agreement between a client and the EAP provider.

Responsibilities:
- Manage contract lifecycle (activate, renew, expire, terminate)
- Validate contract terms and dates
- Track billing state
- Determine service availability

Key Invariants:
- Contract dates must form a valid range
- Termination requires a valid reason
- Billing values must be non-negative
- Only active contracts permit service delivery

Design Notes:
- Aggregate root for all contract-related rules
- Identity-based equality (ContractId)
- Pure domain entity (no persistence or framework concerns)
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from app.domain.value_objects.core import ContractId, TenantId, ClientId, DateRange, Money
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus
from app.domain.events import DomainEvent, ContractRenewed, ContractTerminated
from app.domain.exceptions import DomainError
from app.shared.utils.datetime import utc_now

@dataclass
class ContractEntity:
    # Required fields (no defaults)
    _id: ContractId
    _tenant_id: TenantId
    _client_id: ClientId
    _period: DateRange  # Value Object
    _billing_rate: Money  # Value Object
    _payment_frequency: PaymentFrequency
    _payment_status: PaymentStatus
    _status: ContractStatus
    _is_auto_renew: bool
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields (with defaults)
    _last_billing_date: date | None = None
    _next_billing_date: date | None = None
    _signed_by: str | None = None
    _signed_at: datetime | None = None
    _termination_reason: str | None = None
    _deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    
    def renew(self, new_end_date: date, new_rate: Money | None = None) -> None:
        if new_end_date <= self._period.end_date.date():
            raise DomainError("New end date must be after current")
        # Convert date to datetime at end of day for the new period
        new_end_datetime = datetime.combine(new_end_date, time.max).replace(tzinfo=self._period.end_date.tzinfo)
        self._period = DateRange(self._period.start_date, new_end_datetime)
        if new_rate:
            self._billing_rate = new_rate
        self._status = ContractStatus.RENEWED
        now = utc_now()
        self._updated_at = now
        self._events.append(ContractRenewed(occurred_at=now, contract_id=self._id, new_end_date=new_end_datetime))
    
    def terminate(self, reason: str) -> None:
        if not reason:
            raise DomainError("Termination requires reason")
        self._status = ContractStatus.TERMINATED
        self._termination_reason = reason
        now = utc_now()
        self._updated_at = now
        self._deleted_at = now
        self._events.append(ContractTerminated(occurred_at=now, contract_id=self._id, reason=reason))
    
    def is_active(self) -> bool:
        """Check if contract is active. Returns True for ACTIVE or RENEWED status."""
        if self._status not in (ContractStatus.ACTIVE, ContractStatus.RENEWED):
            return False
        return self._period.contains(utc_now())
    
    def days_remaining(self) -> int:
        """Returns days remaining in contract. Negative if expired."""
        return (self._period.end_date - utc_now()).days