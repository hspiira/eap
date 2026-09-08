"""
Contract Use Cases

Application services for Contract aggregate operations.
Refactored to use base use case classes.
"""

from datetime import date, timedelta

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus, PricingModel
from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    DateRange,
    Money,
    TenantId,
)
from app.domain.value_objects.pricing import ContractPricing
from app.shared.utils.datetime import utc_now

# Lifecycle / single-field updates dispatched via TransitionUseCase + ContractTransition.


class CreateContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Use case for creating a new contract."""

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)

    async def execute(
        self,
        contract_id: ContractId,
        tenant_id: TenantId,
        client_id: ClientId,
        start_date: date,
        end_date: date,
        billing_rate: Money,
        payment_frequency: PaymentFrequency,
        is_auto_renew: bool = False,
        pricing: ContractPricing | None = None,
    ) -> ContractEntity:
        """Create a new contract."""
        period = DateRange(start_date=start_date, end_date=end_date)
        await _reject_overlap(self.repository, tenant_id, client_id, period)
        # A flat periodic charge is a retainer. Saying so at creation means the
        # invoice preview has something to compute from, rather than refusing
        # until somebody configures pricing separately.
        pricing = pricing or ContractPricing(
            model=PricingModel.RETAINER, retainer_amount=billing_rate
        )

        # Create contract entity
        contract = ContractEntity(
            id=contract_id,
            tenant_id=tenant_id,
            client_id=client_id,
            period=period,
            billing_rate=billing_rate,
            payment_frequency=payment_frequency,
            payment_status=PaymentStatus.PENDING,
            status=ContractStatus.DRAFT,
            is_auto_renew=is_auto_renew,
            last_billing_date=None,
            next_billing_date=None,
            signed_by=None,
            signed_at=None,
            termination_reason=None,
            created_at=utc_now(),
            updated_at=utc_now(),
            deleted_at=None,
            pricing=pricing,
        )
        contract.record_created()

        return await self._save_and_publish_events(contract)


async def _reject_overlap(
    repository: ContractRepository,
    tenant_id: TenantId,
    client_id: ClientId,
    period: DateRange,
    *,
    exclude_id: ContractId | None = None,
) -> None:
    """One client, one term at a time.

    Two live terms over the same days make every question about that period
    ambiguous, starting with which one a session belongs to: sessions carry a
    client and a date, not a contract.
    """
    conflicts = await repository.find_overlapping(
        tenant_id,
        client_id,
        start_date=period.start_date,
        end_date=period.end_date,
        exclude_id=exclude_id,
    )
    if conflicts:
        clash = conflicts[0]
        raise ConflictError(
            f"This client already has a contract running "
            f"{clash.period.start_date} to {clash.period.end_date}"
        )


class RenewContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Close a term and open the one that follows it.

    Not a TransitionUseCase: renewal produces a second aggregate, and that use
    case loads, mutates and saves exactly one.
    """

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)
        self.contract_repository = contract_repository

    async def execute(
        self,
        contract_id: ContractId,
        *,
        successor_id: ContractId,
        new_end_date: date,
        new_rate: Money | None = None,
        reference: str | None = None,
    ) -> ContractEntity:
        contract = await self.contract_repository.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError(
                f"Contract not found: {contract_id.value}", "Contract", contract_id.value
            )
        successor_period = DateRange(
            start_date=contract.period.end_date + timedelta(days=1), end_date=new_end_date
        )
        await _reject_overlap(
            self.contract_repository,
            contract.tenant_id,
            contract.client_id,
            successor_period,
            exclude_id=contract.id,
        )
        successor = contract.renew(
            successor_id=successor_id,
            new_end_date=new_end_date,
            new_rate=new_rate,
            reference=reference,
        )
        await self._save_and_publish_events(contract)
        return await self._save_and_publish_events(successor)


class UpdateContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Composite update for Contract (multiple optional fields)."""

    async def execute(
        self,
        contract_id: ContractId,
        billing_rate: Money | None = None,
        payment_frequency: PaymentFrequency | None = None,
        is_auto_renew: bool | None = None,
    ) -> ContractEntity:
        contract = await self._get_entity_or_raise(contract_id, "Contract")
        if billing_rate is not None:
            contract.update_billing_rate(billing_rate)
        if payment_frequency is not None:
            contract.update_payment_frequency(payment_frequency)
        if is_auto_renew is not None:
            contract.update_auto_renew(is_auto_renew)
        return await self._save_and_publish_events(contract)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Use case for retrieving contracts."""

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)
        self.contract_repository = contract_repository

    async def execute(self, contract_id: ContractId) -> ContractEntity | None:
        """Get contract by ID."""
        return await self.repository.get_by_id(contract_id)

    async def execute_by_client(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractEntity]:
        """Get all contracts for a client."""
        return await self.contract_repository.get_by_client_id(tenant_id, client_id)

    async def execute_active_by_client(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> ContractEntity | None:
        """Get active contract for a client."""
        return await self.contract_repository.get_active_by_client_id(tenant_id, client_id)
