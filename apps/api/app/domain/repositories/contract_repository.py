"""
Contract Repository Interface

Defines the contract for Contract data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientId, ContractId, TenantId


@dataclass(frozen=True)
class ContractMetricsRow:
    """One contract term's covered-service count and completed-session spend."""

    contract_id: str
    services: int
    sessions: int
    sessions_priced: int
    spent: int


class ContractRepository(BaseRepository[ContractEntity, ContractId]):
    """
    Repository interface for Contract aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_client_id(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractEntity]:
        """
        Get all contracts for a client within a tenant.

        Args:
            tenant_id: Tenant identifier
            client_id: Client identifier

        Returns:
            List of ContractEntity for the client
        """
        pass

    @abstractmethod
    async def find_overlapping(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        *,
        start_date: date,
        end_date: date,
        exclude_id: ContractId | None = None,
    ) -> list[ContractEntity]:
        """Terms for this client whose period intersects the given one.

        Terminated terms do not conflict: the point of terminating one is to
        replace it, often on a period that starts inside the old one.
        """
        pass

    @abstractmethod
    async def get_active_by_client_id(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> ContractEntity | None:
        """
        Get active contract for a client within a tenant.

        Args:
            tenant_id: Tenant identifier
            client_id: Client identifier

        Returns:
            Active ContractEntity if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        is_auto_renew: bool | None = None,
        ends_from: date | None = None,
        ends_to: date | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ContractEntity]:
        """
        List contracts with filtering, searching, and pagination.

        Args:
            tenant_id: Tenant identifier
            client_id: Filter by client identifier
            status: Filter by contract status
            payment_status: Filter by payment status
            search: Search in contract details (not implemented in basic version)
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order

        Returns:
            Sequence of ContractEntity
        """

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        is_auto_renew: bool | None = None,
        ends_from: date | None = None,
        ends_to: date | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count contracts matching filters.

        Args:
            tenant_id: Tenant identifier
            client_id: Filter by client identifier
            status: Filter by contract status
            payment_status: Filter by payment status
            search: Search in contract details

        Returns:
            Total count
        """

    @abstractmethod
    async def get_metrics_for_client(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractMetricsRow]:
        """Count each contract's covered services and sum its completed sessions' cost.

        A session carries no contract, only a client and a date, so it is
        attributed to the term its date falls inside; overlapping terms both
        count the same session.
        """
