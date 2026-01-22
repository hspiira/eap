"""
Client Use Cases

Application services for Client aggregate operations.
"""

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    Email,
    IndustryId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


class CreateClientUseCase:
    """Use case for creating a new client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(
        self,
        client_id: ClientId,
        tenant_id: TenantId,
        name: str,
        contact_info: ContactInfo,
        billing_address: Address | None = None,
        industry_id: IndustryId | None = None,
        parent_client_id: ClientId | None = None,
    ) -> ClientEntity:
        """
        Create a new client.

        Args:
            client_id: Unique client identifier
            tenant_id: Tenant identifier
            name: Client name
            contact_info: Contact information
            billing_address: Billing address (optional)
            industry_id: Industry identifier (optional)
            parent_client_id: Parent client identifier (optional)

        Returns:
            Created ClientEntity

        Raises:
            ValueError: If client with name already exists
        """
        # Check if client already exists
        existing = await self.client_repository.get_by_name(tenant_id, name)
        if existing:
            raise ValueError(f"Client with name '{name}' already exists")

        # Create client entity
        client = ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name=name,
            _contact_info=contact_info,
            _billing_address=billing_address,
            _industry_id=industry_id,
            _parent_client_id=parent_client_id,
            _status=BaseStatus.PENDING,
            _is_verified=False,
            _preferred_contact_method=None,
            _created_at=utc_now(),
            _updated_at=utc_now(),
            _deleted_at=None,
        )

        # Save client
        await self.client_repository.save(client)

        return client


class VerifyClientUseCase:
    """Use case for verifying a client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(
        self, client_id: ClientId, verified_by: UserId
    ) -> ClientEntity:
        """
        Verify a client.

        Args:
            client_id: Client identifier
            verified_by: User identifier who verified the client

        Returns:
            Verified ClientEntity

        Raises:
            ValueError: If client not found
        """
        client = await self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError(f"Client {client_id.value} not found")

        client.verify(verified_by)
        client._updated_at = utc_now()
        await self.client_repository.save(client)

        return client


class ActivateClientUseCase:
    """Use case for activating a client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: ClientId) -> ClientEntity:
        """
        Activate a client.

        Args:
            client_id: Client identifier

        Returns:
            Activated ClientEntity

        Raises:
            ValueError: If client not found
            DomainError: If client cannot be activated (e.g., no contact info)
        """
        client = await self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError(f"Client {client_id.value} not found")

        client.activate()
        client._updated_at = utc_now()
        await self.client_repository.save(client)

        return client


class GetClientUseCase:
    """Use case for retrieving a client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: ClientId) -> ClientEntity | None:
        """
        Get client by ID.

        Args:
            client_id: Client identifier

        Returns:
            ClientEntity if found, None otherwise
        """
        return await self.client_repository.get_by_id(client_id)

    async def execute_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ClientEntity | None:
        """
        Get client by name within a tenant.

        Args:
            tenant_id: Tenant identifier
            name: Client name

        Returns:
            ClientEntity if found, None otherwise
        """
        return await self.client_repository.get_by_name(tenant_id, name)
