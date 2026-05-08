"""
Contract Use Cases

Application services for Contract aggregate operations.
Refactored to use base use case classes.
"""

from datetime import date, datetime

from app.application.use_cases.base import (
    BaseUseCase,
    create_activate_use_case,
    create_archive_use_case,
    create_restore_use_case,
    create_terminate_use_case,
)
from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    DateRange,
    Money,
    TenantId,
)
from app.shared.utils.datetime import utc_now


# =============================================================================
# LIFECYCLE USE CASES (Using Base Factories)
# =============================================================================


class ActivateContractUseCase:
    """Use case for activating a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self._use_case = create_activate_use_case(contract_repository, "Contract")

    async def execute(self, contract_id: ContractId) -> ContractEntity:
        return await self._use_case.execute(contract_id)


class TerminateContractUseCase:
    """Use case for terminating a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self._use_case = create_terminate_use_case(contract_repository, "Contract")

    async def execute(self, contract_id: ContractId, reason: str) -> ContractEntity:
        return await self._use_case.execute(contract_id, reason=reason)


class ArchiveContractUseCase:
    """Use case for archiving a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self._use_case = create_archive_use_case(contract_repository, "Contract")

    async def execute(self, contract_id: ContractId) -> ContractEntity:
        return await self._use_case.execute(contract_id)


class RestoreContractUseCase:
    """Use case for restoring a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self._use_case = create_restore_use_case(contract_repository, "Contract")

    async def execute(self, contract_id: ContractId) -> ContractEntity:
        return await self._use_case.execute(contract_id)


# =============================================================================
# CREATE USE CASE
# =============================================================================


class CreateContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Use case for creating a new contract."""

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)

    async def execute(
        self,
        contract_id: ContractId,
        tenant_id: TenantId,
        client_id: ClientId,
        start_date: datetime,
        end_date: datetime,
        billing_rate: Money,
        payment_frequency: PaymentFrequency,
        is_auto_renew: bool = False,
    ) -> ContractEntity:
        """Create a new contract."""
        # Create DateRange value object
        period = DateRange(start_date=start_date, end_date=end_date)

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
        )

        return await self._save_and_publish_events(contract)


# =============================================================================
# SPECIALIZED COMMAND USE CASES
# =============================================================================


class SignContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Use case for signing a contract."""

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)

    async def execute(self, contract_id: ContractId, signed_by: str) -> ContractEntity:
        """Sign a contract."""
        contract = await self._get_entity_or_raise(contract_id, "Contract")
        contract.sign(signed_by)
        return await self._save_and_publish_events(contract)


class RenewContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Use case for renewing a contract."""

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)

    async def execute(
        self,
        contract_id: ContractId,
        new_end_date: date,
        new_rate: Money | None = None,
    ) -> ContractEntity:
        """Renew a contract."""
        contract = await self._get_entity_or_raise(contract_id, "Contract")
        contract.renew(new_end_date, new_rate)
        return await self._save_and_publish_events(contract)


# =============================================================================
# UPDATE USE CASES
# =============================================================================


class UpdateContractUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Use case for updating contract information."""

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)

    async def execute(
        self,
        contract_id: ContractId,
        billing_rate: Money | None = None,
        payment_frequency: PaymentFrequency | None = None,
        is_auto_renew: bool | None = None,
    ) -> ContractEntity:
        """Update contract information."""
        contract = await self._get_entity_or_raise(contract_id, "Contract")

        if billing_rate is not None:
            contract.update_billing_rate(billing_rate)
        if payment_frequency is not None:
            contract.update_payment_frequency(payment_frequency)
        if is_auto_renew is not None:
            contract.update_auto_renew(is_auto_renew)

        return await self._save_and_publish_events(contract)


class UpdateContractPaymentStatusUseCase(BaseUseCase[ContractEntity, ContractId]):
    """Use case for updating contract payment status."""

    def __init__(self, contract_repository: ContractRepository):
        super().__init__(contract_repository)

    async def execute(
        self, contract_id: ContractId, payment_status: PaymentStatus
    ) -> ContractEntity:
        """Update contract payment status."""
        contract = await self._get_entity_or_raise(contract_id, "Contract")
        contract.update_payment_status(payment_status)
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
        return await self.contract_repository.get_active_by_client_id(
            tenant_id, client_id
        )
