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

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta

from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus, PricingModel
from app.domain.events import (
    ContractCreated,
    ContractRenewed,
    ContractSigned,
    ContractStatusChanged,
    ContractTerminated,
    ContractUpdated,
    DomainEvent,
)
from app.domain.exceptions import ConflictError, DomainError
from app.domain.value_objects.core import ClientId, ContractId, DateRange, Money, TenantId
from app.domain.value_objects.pricing import ContractPricing
from app.shared.utils.datetime import utc_now


def _pricing_with_standing_charge(pricing: ContractPricing, rate: Money) -> ContractPricing:
    """The same pricing with its standing charge moved to `rate`."""
    if pricing.model == PricingModel.RETAINER:
        return replace(pricing, retainer_amount=rate)
    if pricing.model == PricingModel.FRAMEWORK:
        return replace(pricing, deposit_amount=rate)
    if pricing.model == PricingModel.ADMIN_UTILISATION:
        return replace(pricing, admin_fee_floor=rate)
    raise DomainError(
        f"{pricing.model.value} pricing has no standing charge; edit its rate card instead"
    )


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
    reference: str | None = None
    renewed_from_id: ContractId | None = None
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
        self.events.append(
            ContractUpdated(occurred_at=utc_now(), contract_id=self.id, field="pricing")
        )

    @property
    def pricing_model(self) -> PricingModel | None:
        return self.pricing.model if self.pricing else None

    def headline_rate(self) -> Money | None:
        """The one figure that stands for this contract's price, if there is one.

        `pricing` is the agreement; this is a reading of it for a list column.
        Three of the five models have a standing charge and it is that.
        Fee-for-service has only a rate card, so there is no single number and
        this returns None rather than inventing one: the caller shows the model
        instead.
        """
        if self.pricing is None:
            return self.billing_rate
        if self.pricing.model == PricingModel.RETAINER:
            return self.pricing.retainer_amount
        if self.pricing.model == PricingModel.FRAMEWORK:
            return self.pricing.deposit_amount
        if self.pricing.model == PricingModel.ADMIN_UTILISATION:
            return self.pricing.admin_fee_floor
        return None

    def renew(
        self,
        *,
        successor_id: ContractId,
        new_end_date: date,
        new_rate: Money | None = None,
        reference: str | None = None,
    ) -> "ContractEntity":
        """Close this term and return the one that follows it.

        Renewal used to move this term's end date and overwrite its rate, so a
        contract renewed three times was one row at one price and the earlier
        terms were gone. The successor starts the day after this one ends and
        points back through `renewed_from_id`, which is what makes the history
        readable as a chain.
        """
        if new_end_date <= self.period.end_date:
            raise DomainError("New end date must be after current")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot renew a terminated contract")
        now = utc_now()
        # A new rate is a change to the standing charge, so it has to move in
        # the pricing too: that is what the invoice is computed from.
        successor_pricing = self.pricing
        if new_rate is not None and successor_pricing is not None:
            successor_pricing = _pricing_with_standing_charge(successor_pricing, new_rate)
        successor = ContractEntity(
            id=successor_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            period=DateRange(self.period.end_date + timedelta(days=1), new_end_date),
            billing_rate=new_rate or self.billing_rate,
            payment_frequency=self.payment_frequency,
            payment_status=PaymentStatus.PENDING,
            status=ContractStatus.DRAFT,
            is_auto_renew=self.is_auto_renew,
            reference=reference,
            renewed_from_id=self.id,
            pricing=successor_pricing,
            created_at=now,
            updated_at=now,
        )
        successor.record_created()
        self.status = ContractStatus.RENEWED
        self.updated_at = now
        self.events.append(
            ContractRenewed(occurred_at=now, contract_id=self.id, new_end_date=new_end_date)
        )
        return successor

    def activate(self) -> None:
        """Activate a draft or pending contract"""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted contract")
        if self.status == ContractStatus.ACTIVE:
            raise ConflictError("Contract is already active")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot activate terminated contract")
        if self.status == ContractStatus.EXPIRED:
            raise DomainError("Cannot activate expired contract")
        previous = self.status
        self.status = ContractStatus.ACTIVE
        self.updated_at = utc_now()
        self._record_status_change(previous)

    def sign(self, signed_by: str) -> None:
        """Sign a contract"""
        if not signed_by:
            raise DomainError("Signer name is required")
        if self.deleted_at:
            raise DomainError("Cannot sign deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot sign terminated contract")
        if self.signed_at:
            raise ConflictError("Contract is already signed")
        previous = self.status
        self.signed_by = signed_by
        self.signed_at = utc_now()
        self.updated_at = utc_now()
        # Auto-activate when signed
        if self.status in (ContractStatus.DRAFT, ContractStatus.PENDING):
            self.status = ContractStatus.ACTIVE
        self.events.append(
            ContractSigned(occurred_at=utc_now(), contract_id=self.id, signed_by=signed_by)
        )
        self._record_status_change(previous)

    def terminate(self, reason: str) -> None:
        """End a contract for cause, keeping the record of it.

        Termination does not soft-delete. It is a commercial fact about a real
        agreement, and the row is where a dispute is argued from; deleting it
        removes the contract from every list somebody would look in.
        """
        if not reason:
            raise DomainError("Termination requires reason")
        if self.deleted_at:
            raise DomainError("Cannot terminate deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise ConflictError("Contract is already terminated")
        self.status = ContractStatus.TERMINATED
        self.termination_reason = reason
        now = utc_now()
        self.updated_at = now
        self.events.append(ContractTerminated(occurred_at=now, contract_id=self.id, reason=reason))

    def archive(self) -> None:
        """Write down the lapse that `effective_status` already derives.

        Redundant now that lapsing is derived, and kept because its callers and
        the meaning of "archive" for a contract are a separate question: the
        status enum has no ARCHIVED member, which is why this overloads EXPIRED.
        """
        if self.deleted_at:
            raise DomainError("Cannot archive deleted contract")
        previous = self.status
        if self.period.end_date < utc_now().date() and self.status == ContractStatus.ACTIVE:
            self.status = ContractStatus.EXPIRED
        self.updated_at = utc_now()
        self._record_status_change(previous)

    def restore(self) -> None:
        """Restore a terminated or expired contract"""
        # Check if contract is already active and not deleted
        if self.status == ContractStatus.ACTIVE and self.deleted_at is None:
            raise ConflictError("Contract is already active and does not need restoration")
        previous = self.status
        # Restore soft-deleted contract
        if self.deleted_at:
            self.deleted_at = None
        # Restore terminated/expired contract to active if period is still valid
        if self.status in (ContractStatus.TERMINATED, ContractStatus.EXPIRED):
            if self.period.end_date >= utc_now().date():
                self.status = ContractStatus.ACTIVE
                self.termination_reason = None
        self.updated_at = utc_now()
        self._record_status_change(previous)

    def update_billing_rate(self, new_rate: Money) -> None:
        """Change the standing charge, in the pricing that defines it.

        Writing only the old `billing_rate` column would leave the invoice
        preview computing from the previous figure, because it reads `pricing`.
        A model with no standing charge has to be edited as pricing.
        """
        if self.deleted_at:
            raise DomainError("Cannot update billing rate for deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update billing rate for terminated contract")
        if self.pricing is not None:
            self.pricing = _pricing_with_standing_charge(self.pricing, new_rate)
        self.billing_rate = new_rate
        self.updated_at = utc_now()
        self.events.append(
            ContractUpdated(occurred_at=utc_now(), contract_id=self.id, field="billing_rate")
        )

    def update_payment_frequency(self, frequency: PaymentFrequency) -> None:
        """Update payment frequency"""
        if self.deleted_at:
            raise DomainError("Cannot update payment frequency for deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update payment frequency for terminated contract")
        self.payment_frequency = frequency
        self.updated_at = utc_now()
        self.events.append(
            ContractUpdated(occurred_at=utc_now(), contract_id=self.id, field="payment_frequency")
        )

    def update_payment_status(self, payment_status: PaymentStatus) -> None:
        """Update payment status"""
        if self.deleted_at:
            raise DomainError("Cannot update payment status for deleted contract")
        self.payment_status = payment_status
        self.updated_at = utc_now()
        self.events.append(
            ContractUpdated(occurred_at=utc_now(), contract_id=self.id, field="payment_status")
        )

    def update_auto_renew(self, is_auto_renew: bool) -> None:
        """Update auto-renew setting"""
        if self.deleted_at:
            raise DomainError("Cannot update auto-renew for deleted contract")
        if self.status == ContractStatus.TERMINATED:
            raise DomainError("Cannot update auto-renew for terminated contract")
        self.is_auto_renew = is_auto_renew
        self.updated_at = utc_now()
        self.events.append(
            ContractUpdated(occurred_at=utc_now(), contract_id=self.id, field="is_auto_renew")
        )

    def record_created(self) -> None:
        """Announce this contract as newly created. Called by the create use case."""
        self.events.append(
            ContractCreated(occurred_at=utc_now(), contract_id=self.id, client_id=self.client_id)
        )

    def _record_status_change(self, previous: ContractStatus) -> None:
        """Record a lifecycle move."""
        if previous == self.status:
            return
        self.events.append(
            ContractStatusChanged(
                occurred_at=utc_now(),
                contract_id=self.id,
                from_status=previous.value,
                to_status=self.status.value,
            )
        )

    def effective_status(self) -> ContractStatus:
        """The status as at today, rather than the one last written down.

        Nothing sweeps contracts when a term runs out, so a live contract keeps
        its ACTIVE row for years after it ended and the screens showed a green
        badge beside a red "Ended". Lapsing is a fact about the dates and is
        derived here; the decisions a person makes, draft, active, terminated,
        stay stored.
        """
        lapsable = (ContractStatus.ACTIVE, ContractStatus.RENEWED, ContractStatus.PENDING)
        if self.status in lapsable and self.period.end_date < utc_now().date():
            return ContractStatus.EXPIRED
        return self.status

    def is_active(self) -> bool:
        """Check if contract is active. Returns True for ACTIVE or RENEWED status."""
        if self.status not in (ContractStatus.ACTIVE, ContractStatus.RENEWED):
            return False
        return self.period.contains(utc_now().date())

    def days_remaining(self) -> int:
        """Returns whole days left in the term. Zero on the last day, negative once past."""
        return (self.period.end_date - utc_now().date()).days

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()
