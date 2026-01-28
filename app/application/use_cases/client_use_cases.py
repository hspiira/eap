"""
Client Use Cases

Application services for Client aggregate operations.
Refactored to use base use case classes to eliminate boilerplate.
"""

from app.application.use_cases.base import BaseUseCase, EntityLifecycleUseCase
from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ContactMethod
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    IndustryId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


# =============================================================================
# CREATE USE CASE (special - not a lifecycle operation)
# =============================================================================


class CreateClientUseCase(BaseUseCase[ClientEntity, ClientId]):
    """Use case for creating a new client."""

    def __init__(self, client_repository: ClientRepository):
        super().__init__(client_repository)
        self.client_repository = client_repository

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
        """
        if not code or len(code) < 3 or len(code) > 5:
            raise ValueError("Client code must be 3-5 characters")
        
        existing = await self.client_repository.get_by_name(tenant_id, name)
        if existing:
            raise ValueError(f"Client with name '{name}' already exists")

        client = ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name=name,
            _code=code,
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

        return await self._save_and_publish_events(client)


# =============================================================================
# LIFECYCLE USE CASES (using base class)
# =============================================================================


class VerifyClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for verifying a client."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, verified_by: UserId, **kwargs) -> None:
        entity.verify(verified_by)

    async def execute(self, client_id: ClientId, verified_by: UserId) -> ClientEntity:
        """Execute with required verified_by parameter."""
        return await super().execute(client_id, verified_by=verified_by)


class ActivateClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for activating a client."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, *args, **kwargs) -> None:
        entity.activate()


class DeactivateClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for deactivating a client."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, reason: str | None = None, **kwargs) -> None:
        entity.deactivate(reason)

    async def execute(self, client_id: ClientId, reason: str | None = None) -> ClientEntity:
        """Execute with optional reason parameter."""
        return await super().execute(client_id, reason=reason)


class SuspendClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for suspending a client."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, reason: str, **kwargs) -> None:
        entity.suspend(reason)

    async def execute(self, client_id: ClientId, reason: str) -> ClientEntity:
        """Execute with required reason parameter."""
        return await super().execute(client_id, reason=reason)


class TerminateClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for terminating a client."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, reason: str, **kwargs) -> None:
        entity.terminate(reason)

    async def execute(self, client_id: ClientId, reason: str) -> ClientEntity:
        """Execute with required reason parameter."""
        return await super().execute(client_id, reason=reason)


class ArchiveClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for archiving a client."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, *args, **kwargs) -> None:
        entity.archive()


class RestoreClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for restoring a client."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, *args, **kwargs) -> None:
        entity.restore()


# =============================================================================
# UPDATE USE CASES (using base class)
# =============================================================================


class UpdateClientUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for updating client basic information."""

    entity_name = "Client"

    async def _perform_action(
        self,
        entity: ClientEntity,
        name: str | None = None,
        preferred_contact_method: ContactMethod | None = None,
        **kwargs,
    ) -> None:
        if name is not None:
            entity.update_name(name)
        if preferred_contact_method is not None:
            entity.update_preferred_contact_method(preferred_contact_method)

    async def execute(
        self,
        client_id: ClientId,
        name: str | None = None,
        preferred_contact_method: ContactMethod | None = None,
    ) -> ClientEntity:
        """Execute with optional update parameters."""
        return await super().execute(
            client_id,
            name=name,
            preferred_contact_method=preferred_contact_method,
        )


class UpdateClientContactInfoUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for updating client contact information."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, contact_info: ContactInfo, **kwargs) -> None:
        entity.update_contact_info(contact_info)

    async def execute(self, client_id: ClientId, contact_info: ContactInfo) -> ClientEntity:
        """Execute with required contact_info parameter."""
        return await super().execute(client_id, contact_info=contact_info)


class UpdateClientBillingAddressUseCase(EntityLifecycleUseCase[ClientEntity, ClientId]):
    """Use case for updating client billing address."""

    entity_name = "Client"

    async def _perform_action(self, entity: ClientEntity, billing_address: Address | None, **kwargs) -> None:
        entity.update_billing_address(billing_address)

    async def execute(self, client_id: ClientId, billing_address: Address | None) -> ClientEntity:
        """Execute with billing_address parameter (can be None to clear)."""
        return await super().execute(client_id, billing_address=billing_address)


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
