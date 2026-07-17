"""
Client Use Cases

Application services for Client aggregate operations.
Refactored to use base use case classes to eliminate boilerplate.
"""

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ClientTier, ContactMethod
from app.domain.exceptions import SubscriptionLimitError
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    IndustryId,
    TenantId,
)
from app.shared.utils.datetime import utc_now

# =============================================================================
# CREATE USE CASE (special - not a lifecycle operation)
# =============================================================================


class CreateClientUseCase(BaseUseCase[ClientEntity, ClientId]):
    """Use case for creating a new client."""

    def __init__(
        self,
        client_repository: ClientRepository,
        tenant_repository: TenantRepository | None = None,
    ):
        super().__init__(client_repository)
        self.client_repository = client_repository
        self.tenant_repository = tenant_repository

    async def execute(
        self,
        client_id: ClientId,
        tenant_id: TenantId,
        name: str,
        code: str,
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
            code: Client code (3-5 characters, unique per tenant)
            contact_info: Contact information
            billing_address: Billing address (optional)
            industry_id: Industry identifier (optional)
            parent_client_id: Parent client identifier (optional)

        Returns:
            Created ClientEntity

        Raises:
            ValueError: If client with name or code already exists
            SubscriptionLimitError: If tenant client limit reached
        """
        if self.tenant_repository:
            tenant = await self.tenant_repository.get_by_id(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant not found: {tenant_id.value}")
            from app.core.config import settings as _settings  # local import to avoid cycle

            if getattr(_settings, "ENFORCE_SUBSCRIPTION_LIMITS", False):
                client_count = await self.client_repository.count(tenant_id=tenant_id)
                if not tenant.can_create_clients(client_count):
                    raise SubscriptionLimitError(
                        "Tenant client limit reached; upgrade subscription to add more clients."
                    )

        if not code or len(code) < 3 or len(code) > 5:
            raise ValueError("Client code must be 3-5 characters")

        existing = await self.client_repository.get_by_name(tenant_id, name)
        if existing:
            raise ValueError(f"Client with name '{name}' already exists")

        client = ClientEntity(
            id=client_id,
            tenant_id=tenant_id,
            name=name,
            code=code,
            contact_info=contact_info,
            billing_address=billing_address,
            industry_id=industry_id,
            parent_client_id=parent_client_id,
            status=BaseStatus.PENDING,
            is_verified=False,
            preferred_contact_method=None,
            created_at=utc_now(),
            updated_at=utc_now(),
            deleted_at=None,
        )

        return await self._save_and_publish_events(client)


# Lifecycle and single-field updates dispatched via TransitionUseCase + ClientTransition.
# UpdateClientUseCase (composite/partial) kept below.


class UpdateClientUseCase(BaseUseCase[ClientEntity, ClientId]):
    """Composite update for Client (multiple optional fields).

    Bespoke because partial updates touch multiple entity methods conditionally.
    Single-method updates flow through TransitionUseCase + ClientTransition.
    """

    async def execute(
        self,
        client_id: ClientId,
        name: str | None = None,
        preferred_contact_method: ContactMethod | None = None,
        tier: ClientTier | None = None,
    ) -> ClientEntity:
        client = await self._get_entity_or_raise(client_id, "Client")
        if name is not None:
            client.update_name(name)
        if preferred_contact_method is not None:
            client.update_preferred_contact_method(preferred_contact_method)
        if tier is not None:
            client.update_tier(tier)
        return await self._save_and_publish_events(client)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetClientUseCase(BaseUseCase[ClientEntity, ClientId]):
    """Use case for retrieving a client."""

    def __init__(self, client_repository: ClientRepository):
        super().__init__(client_repository)
        self.client_repository = client_repository

    async def execute(self, client_id: ClientId) -> ClientEntity | None:
        """
        Get client by ID.

        Args:
            client_id: Client identifier

        Returns:
            ClientEntity if found, None otherwise
        """
        return await self.repository.get_by_id(client_id)

    async def execute_by_name(self, tenant_id: TenantId, name: str) -> ClientEntity | None:
        """
        Get client by name within a tenant.

        Args:
            tenant_id: Tenant identifier
            name: Client name

        Returns:
            ClientEntity if found, None otherwise
        """
        return await self.client_repository.get_by_name(tenant_id, name)
