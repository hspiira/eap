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
    
    def activate(self) -> None:
        """Activate a draft or pending contract"""
        if self._deleted_at:
            raise DomainError("Cannot activate deleted contract")
        if self._status == ContractStatus.ACTIVE:
            raise DomainError("Contract is already active")
        if self._status == ContractStatus.TERMINATED:
            raise DomainError("Cannot activate terminated contract")
        if self._status == ContractStatus.EXPIRED:
            raise DomainError("Cannot activate expired contract")
        self._status = ContractStatus.ACTIVE
        self._updated_at = utc_now()
    
    def sign(self, signed_by: str) -> None:
        """Sign a contract"""
        if not signed_by:
            raise DomainError("Signer name is required")
        if self._deleted_at:
            raise DomainError("Cannot sign deleted contract")
        if self._status == ContractStatus.TERMINATED:
            raise DomainError("Cannot sign terminated contract")
        if self._signed_at:
            raise DomainError("Contract is already signed")
        self._signed_by = signed_by
        self._signed_at = utc_now()
        self._updated_at = utc_now()
        # Auto-activate when signed
        if self._status in (ContractStatus.DRAFT, ContractStatus.PENDING):
            self._status = ContractStatus.ACTIVE
    
    def terminate(self, reason: str) -> None:
        """Terminate a contract"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self._deleted_at:
            raise DomainError("Contract is already terminated")
        if self._status == ContractStatus.TERMINATED:
            raise DomainError("Contract is already terminated")
        self._status = ContractStatus.TERMINATED
        self._termination_reason = reason
        now = utc_now()
        self._updated_at = now
        self._deleted_at = now
        self._events.append(ContractTerminated(occurred_at=now, contract_id=self._id, reason=reason))
    
    def archive(self) -> None:
        """Archive a contract (mark as expired if past end date)"""
        if self._deleted_at:
            raise DomainError("Cannot archive deleted contract")
        # Archive is a soft operation - mark expired contracts
        if self._period.end_date < utc_now() and self._status == ContractStatus.ACTIVE:
            self._status = ContractStatus.EXPIRED
        self._updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore a terminated or expired contract"""
        if self._deleted_at:
            raise DomainError("Cannot restore deleted contract")
        # Check if contract is already active and not deleted
        if self._status == ContractStatus.ACTIVE and self._deleted_at is None:
            raise DomainError("Contract is already active and does not need restoration")
        # Restore soft-deleted contract
        if self._deleted_at:
            self._deleted_at = None
        # Restore terminated/expired contract to active if period is still valid
        if self._status in (ContractStatus.TERMINATED, ContractStatus.EXPIRED):
            if self._period.end_date >= utc_now():
                self._status = ContractStatus.ACTIVE
                self._termination_reason = None
        self._updated_at = utc_now()
    
    def update_billing_rate(self, new_rate: Money) -> None:
        """Update billing rate"""
        if self._deleted_at:
            raise DomainError("Cannot update billing rate for deleted contract")
        if self._status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update billing rate for terminated contract")
        self._billing_rate = new_rate
        self._updated_at = utc_now()
    
    def update_payment_frequency(self, frequency: PaymentFrequency) -> None:
        """Update payment frequency"""
        if self._deleted_at:
            raise DomainError("Cannot update payment frequency for deleted contract")
        if self._status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update payment frequency for terminated contract")
        self._payment_frequency = frequency
        self._updated_at = utc_now()
    
    def update_payment_status(self, payment_status: PaymentStatus) -> None:
        """Update payment status"""
        if self._deleted_at:
            raise DomainError("Cannot update payment status for deleted contract")
        self._payment_status = payment_status
        self._updated_at = utc_now()
    
    def update_auto_renew(self, is_auto_renew: bool) -> None:
        """Update auto-renew setting"""
        if self._deleted_at:
            raise DomainError("Cannot update auto-renew for deleted contract")
        if self._status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update auto-renew for terminated contract")
        self._is_auto_renew = is_auto_renew
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if contract is active. Returns True for ACTIVE or RENEWED status."""
        if self._status not in (ContractStatus.ACTIVE, ContractStatus.RENEWED):
            return False
        return self._period.contains(utc_now())
    
    def days_remaining(self) -> int:
        """Returns days remaining in contract. Negative if expired."""
        return (self._period.end_date - utc_now()).days

    # === Public Properties ===

    @property
    def id(self) -> ContractId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def client_id(self) -> ClientId:
        return self._client_id

    @property
    def period(self) -> DateRange:
        return self._period

    @property
    def billing_rate(self) -> Money:
        return self._billing_rate

    @property
    def payment_frequency(self) -> PaymentFrequency:
        return self._payment_frequency

    @property
    def payment_status(self) -> PaymentStatus:
        return self._payment_status

    @property
    def status(self) -> ContractStatus:
        return self._status

    @property
    def is_auto_renew(self) -> bool:
        return self._is_auto_renew

    @property
    def last_billing_date(self) -> date | None:
        return self._last_billing_date

    @property
    def next_billing_date(self) -> date | None:
        return self._next_billing_date

    @property
    def signed_by(self) -> str | None:
        return self._signed_by

    @property
    def signed_at(self) -> datetime | None:
        return self._signed_at

    @property
    def termination_reason(self) -> str | None:
        return self._termination_reason

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()