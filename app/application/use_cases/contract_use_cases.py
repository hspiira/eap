"""
Contract Use Cases

Application services for Contract aggregate operations.
"""

from datetime import date, datetime

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


class CreateContractUseCase:
    """Use case for creating a new contract."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

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
        """
        Create a new contract.

        Args:
            contract_id: Unique contract identifier
            tenant_id: Tenant identifier
            client_id: Client identifier
            start_date: Contract start date
            end_date: Contract end date
            billing_rate: Billing rate (Money value object)
            payment_frequency: Payment frequency
            is_auto_renew: Whether contract auto-renews

        Returns:
            Created ContractEntity

        Raises:
            ValueError: If dates are invalid
        """
        # Create DateRange value object
        period = DateRange(start_date=start_date, end_date=end_date)

        # Create contract entity
        contract = ContractEntity(
            _id=contract_id,
            _tenant_id=tenant_id,
            _client_id=client_id,
            _period=period,
            _billing_rate=billing_rate,
            _payment_frequency=payment_frequency,
            _payment_status=PaymentStatus.PENDING,
            _status=ContractStatus.DRAFT,
            _is_auto_renew=is_auto_renew,
            _last_billing_date=None,
            _next_billing_date=None,
            _signed_by=None,
            _signed_at=None,
            _termination_reason=None,
            _created_at=utc_now(),
            _updated_at=utc_now(),
            _deleted_at=None,
        )

        # Save contract
        await self.contract_repository.save(contract)

        return contract


class RenewContractUseCase:
    """Use case for renewing a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(
        self,
        contract_id: ContractId,
        new_end_date: date,
        new_rate: Money | None = None,
    ) -> ContractEntity:
        """
        Renew a contract.

        Args:
            contract_id: Contract identifier
            new_end_date: New contract end date
            new_rate: New billing rate (optional)

        Returns:
            Renewed ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If renewal is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        contract.renew(new_end_date, new_rate)
        await self.contract_repository.save(contract)

        return contract


class TerminateContractUseCase:
    """Use case for terminating a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(
        self, contract_id: ContractId, reason: str
    ) -> ContractEntity:
        """
        Terminate a contract.

        Args:
            contract_id: Contract identifier
            reason: Termination reason

        Returns:
            Terminated ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If termination is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        contract.terminate(reason)
        await self.contract_repository.save(contract)

        return contract


class GetContractUseCase:
    """Use case for retrieving contracts."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(self, contract_id: ContractId) -> ContractEntity | None:
        """
        Get contract by ID.

        Args:
            contract_id: Contract identifier

        Returns:
            ContractEntity if found, None otherwise
        """
        return await self.contract_repository.get_by_id(contract_id)

    async def execute_by_client(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractEntity]:
        """
        Get all contracts for a client.

        Args:
            tenant_id: Tenant identifier
            client_id: Client identifier

        Returns:
            List of ContractEntity for the client
        """
        return await self.contract_repository.get_by_client_id(tenant_id, client_id)

    async def execute_active_by_client(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> ContractEntity | None:
        """
        Get active contract for a client.

        Args:
            tenant_id: Tenant identifier
            client_id: Client identifier

        Returns:
            Active ContractEntity if found, None otherwise
        """
        return await self.contract_repository.get_active_by_client_id(
            tenant_id, client_id
        )


class ActivateContractUseCase:
    """Use case for activating a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(self, contract_id: ContractId) -> ContractEntity:
        """
        Activate a contract.

        Args:
            contract_id: Contract identifier

        Returns:
            Activated ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If activation is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        contract.activate()
        contract._updated_at = utc_now()
        await self.contract_repository.save(contract)

        return contract


class SignContractUseCase:
    """Use case for signing a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(
        self, contract_id: ContractId, signed_by: str
    ) -> ContractEntity:
        """
        Sign a contract.

        Args:
            contract_id: Contract identifier
            signed_by: Name of person signing

        Returns:
            Signed ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If signing is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        contract.sign(signed_by)
        await self.contract_repository.save(contract)

        return contract


class ArchiveContractUseCase:
    """Use case for archiving a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(self, contract_id: ContractId) -> ContractEntity:
        """
        Archive a contract.

        Args:
            contract_id: Contract identifier

        Returns:
            Archived ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If archive is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        contract.archive()
        await self.contract_repository.save(contract)

        return contract


class RestoreContractUseCase:
    """Use case for restoring a contract."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(self, contract_id: ContractId) -> ContractEntity:
        """
        Restore a terminated or expired contract.

        Args:
            contract_id: Contract identifier

        Returns:
            Restored ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If restore is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        contract.restore()
        await self.contract_repository.save(contract)

        return contract


class UpdateContractUseCase:
    """Use case for updating contract information."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(
        self,
        contract_id: ContractId,
        billing_rate: Money | None = None,
        payment_frequency: PaymentFrequency | None = None,
        is_auto_renew: bool | None = None,
    ) -> ContractEntity:
        """
        Update contract information.

        Args:
            contract_id: Contract identifier
            billing_rate: New billing rate (optional)
            payment_frequency: New payment frequency (optional)
            is_auto_renew: Auto-renew setting (optional)

        Returns:
            Updated ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If update is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        if billing_rate is not None:
            contract.update_billing_rate(billing_rate)
        if payment_frequency is not None:
            contract.update_payment_frequency(payment_frequency)
        if is_auto_renew is not None:
            contract.update_auto_renew(is_auto_renew)

        await self.contract_repository.save(contract)

        return contract


class UpdateContractPaymentStatusUseCase:
    """Use case for updating contract payment status."""

    def __init__(self, contract_repository: ContractRepository):
        self.contract_repository = contract_repository

    async def execute(
        self, contract_id: ContractId, payment_status: PaymentStatus
    ) -> ContractEntity:
        """
        Update contract payment status.

        Args:
            contract_id: Contract identifier
            payment_status: New payment status

        Returns:
            Updated ContractEntity

        Raises:
            ValueError: If contract not found
            DomainError: If update is invalid
        """
        contract = await self.contract_repository.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id.value} not found")

        contract.update_payment_status(payment_status)
        await self.contract_repository.save(contract)

        return contract
