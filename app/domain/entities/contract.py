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
from app.domain.value_objects.pricing import ContractPricing
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus, PricingModel
from app.domain.events import DomainEvent, ContractRenewed, ContractTerminated
from app.domain.exceptions import DomainError
from app.shared.utils.datetime import utc_now

@dataclass
class ContractEntity:
    # Required fields (no defaults)
    id: ContractId
    tenant_id: TenantId
    client_id: ClientId
    period: DateRange  # Value Object
    billing_rate: Money  # Value Object
    payment_frequency: PaymentFrequency
    payment_status: PaymentStatus
    status: ContractStatus
    is_auto_renew: bool
    created_at: datetime
    updated_at: datetime
    
    # Optional fields (with defaults)
    last_billing_date: date | None = None
    next_billing_date: date | None = None
    signed_by: str | None = None
    signed_at: datetime | None = None
    termination_reason: str | None = None
    deleted_at: datetime | None = None
    pricing: ContractPricing | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def update_pricing(self, pricing: ContractPricing) -> None:
        """Set or replace the contract's pricing configuration."""
        if self.deleted_at:
            raise DomainError("Cannot update pricing for deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update pricing for terminated contract")
        self.pricing = pricing
        self.updated_at = utc_now()

    @property
    def pricing_model(self) -> PricingModel | None:
        return self.pricing.model if self.pricing else None
    
    def renew(self, new_end_date: date, new_rate: Money | None = None) -> None:
        if new_end_date <= self.period.end_date.date():
            raise DomainError("New end date must be after current")
        # Convert date to datetime at end of day for the new period
        new_end_datetime = datetime.combine(new_end_date, time.max).replace(tzinfo=self.period.end_date.tzinfo)
        self.period = DateRange(self.period.start_date, new_end_datetime)
        if new_rate:
            self.billing_rate = new_rate
        self.status = ContractStatus.RENEWED
        now = utc_now()
        self.updated_at = now
        self.events.append(ContractRenewed(occurred_at=now, contract_id=self.id, new_end_date=new_end_datetime))
    
    def activate(self) -> None:
        """Activate a draft or pending contract"""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted contract")
        if self.status == ContractStatus.ACTIVE:
            raise DomainError("Contract is already active")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot activate terminated contract")
        if self.status == ContractStatus.EXPIRED:
            raise DomainError("Cannot activate expired contract")
        self.status = ContractStatus.ACTIVE
        self.updated_at = utc_now()
    
    def sign(self, signed_by: str) -> None:
        """Sign a contract"""
        if not signed_by:
            raise DomainError("Signer name is required")
        if self.deleted_at:
            raise DomainError("Cannot sign deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot sign terminated contract")
        if self.signed_at:
            raise DomainError("Contract is already signed")
        self.signed_by = signed_by
        self.signed_at = utc_now()
        self.updated_at = utc_now()
        # Auto-activate when signed
        if self.status in (ContractStatus.DRAFT, ContractStatus.PENDING):
            self.status = ContractStatus.ACTIVE
    
    def terminate(self, reason: str) -> None:
        """Terminate a contract"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self.deleted_at:
            raise DomainError("Cannot terminate deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Contract is already terminated")
        self.status = ContractStatus.TERMINATED
        self.termination_reason = reason
        now = utc_now()
        self.updated_at = now
        self.deleted_at = now
        self.events.append(ContractTerminated(occurred_at=now, contract_id=self.id, reason=reason))
    
    def archive(self) -> None:
        """Archive a contract (mark as expired if past end date)"""
        if self.deleted_at:
            raise DomainError("Cannot archive deleted contract")
        # Archive is a soft operation - mark expired contracts
        if self.period.end_date < utc_now() and self.status == ContractStatus.ACTIVE:
            self.status = ContractStatus.EXPIRED
        self.updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore a terminated or expired contract"""
        # Check if contract is already active and not deleted
        if self.status == ContractStatus.ACTIVE and self.deleted_at is None:
            raise DomainError("Contract is already active and does not need restoration")
        # Restore soft-deleted contract
        if self.deleted_at:
            self.deleted_at = None
        # Restore terminated/expired contract to active if period is still valid
        if self.status in (ContractStatus.TERMINATED, ContractStatus.EXPIRED):
            if self.period.end_date >= utc_now():
                self.status = ContractStatus.ACTIVE
                self.termination_reason = None
        self.updated_at = utc_now()
    
    def update_billing_rate(self, new_rate: Money) -> None:
        """Update billing rate"""
        if self.deleted_at:
            raise DomainError("Cannot update billing rate for deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update billing rate for terminated contract")
        self.billing_rate = new_rate
        self.updated_at = utc_now()
    
    def update_payment_frequency(self, frequency: PaymentFrequency) -> None:
        """Update payment frequency"""
        if self.deleted_at:
            raise DomainError("Cannot update payment frequency for deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update payment frequency for terminated contract")
        self.payment_frequency = frequency
        self.updated_at = utc_now()
    
    def update_payment_status(self, payment_status: PaymentStatus) -> None:
        """Update payment status"""
        if self.deleted_at:
            raise DomainError("Cannot update payment status for deleted contract")
        self.payment_status = payment_status
        self.updated_at = utc_now()
    
    def update_auto_renew(self, is_auto_renew: bool) -> None:
        """Update auto-renew setting"""
        if self.deleted_at:
            raise DomainError("Cannot update auto-renew for deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update auto-renew for terminated contract")
        self.is_auto_renew = is_auto_renew
        self.updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if contract is active. Returns True for ACTIVE or RENEWED status."""
        if self.status not in (ContractStatus.ACTIVE, ContractStatus.RENEWED):
            return False
        return self.period.contains(utc_now())
    
    def days_remaining(self) -> int:
        """Returns days remaining in contract. Negative if expired."""
        return (self.period.end_date - utc_now()).days

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()