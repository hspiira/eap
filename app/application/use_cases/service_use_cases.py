"""
Service Use Cases

Application services for Service aggregate operations.
"""

from app.domain.entities.service import ServiceEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.value_objects.core import ServiceId, TenantId
from app.shared.utils.datetime import utc_now


class CreateServiceUseCase:
    """Use case for creating a new service."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(
        self,
        service_id: ServiceId,
        tenant_id: TenantId,
        name: str,
        description: str | None = None,
        category: str | None = None,
        duration_minutes: int | None = None,
        is_group_service: bool = False,
        max_participants: int | None = None,
    ) -> ServiceEntity:
        """
        Create a new service.

        Args:
            service_id: Unique service identifier
            tenant_id: Tenant identifier
            name: Service name
            description: Service description (optional)
            category: Service category (optional)
            duration_minutes: Service duration in minutes (optional)
            is_group_service: Whether this is a group service
            max_participants: Maximum participants for group services (optional)

        Returns:
            Created ServiceEntity

        Raises:
            ValueError: If service with name already exists
        """
        # Check if service already exists
        existing = await self.service_repository.get_by_name(tenant_id, name)
        if existing:
            raise ValueError(f"Service with name '{name}' already exists")

        # Create service entity
        service = ServiceEntity(
            _id=service_id,
            _tenant_id=tenant_id,
            _name=name,
            _description=description,
            _status=BaseStatus.PENDING,
            _created_at=utc_now(),
            _updated_at=utc_now(),
            _category=category,
            _duration_minutes=duration_minutes,
            _is_group_service=is_group_service,
            _max_participants=max_participants,
        )

        # Save service
        await self.service_repository.save(service)

        return service


class ActivateServiceUseCase:
    """Use case for activating a service."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(self, service_id: ServiceId) -> ServiceEntity:
        """
        Activate a service.

        Args:
            service_id: Service identifier

        Returns:
            Activated ServiceEntity

        Raises:
            ValueError: If service not found
            DomainError: If activation is invalid
        """
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id.value} not found")

        service.activate()
        service._updated_at = utc_now()
        await self.service_repository.save(service)

        return service


class DeactivateServiceUseCase:
    """Use case for deactivating a service."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(
        self, service_id: ServiceId, reason: str | None = None
    ) -> ServiceEntity:
        """
        Deactivate a service.

        Args:
            service_id: Service identifier
            reason: Deactivation reason (optional)

        Returns:
            Deactivated ServiceEntity

        Raises:
            ValueError: If service not found
            DomainError: If deactivation is invalid
        """
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id.value} not found")

        service.deactivate(reason)
        service._updated_at = utc_now()
        await self.service_repository.save(service)

        return service


class ArchiveServiceUseCase:
    """Use case for archiving a service."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(self, service_id: ServiceId) -> ServiceEntity:
        """
        Archive a service.

        Args:
            service_id: Service identifier

        Returns:
            Archived ServiceEntity

        Raises:
            ValueError: If service not found
            DomainError: If archive is invalid
        """
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id.value} not found")

        service.archive()
        await self.service_repository.save(service)

        return service


class RestoreServiceUseCase:
    """Use case for restoring a service."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(self, service_id: ServiceId) -> ServiceEntity:
        """
        Restore an archived or soft-deleted service.

        Args:
            service_id: Service identifier

        Returns:
            Restored ServiceEntity

        Raises:
            ValueError: If service not found
            DomainError: If restore is invalid
        """
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id.value} not found")

        service.restore()
        await self.service_repository.save(service)

        return service


class UpdateServiceUseCase:
    """Use case for updating service information."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(
        self,
        service_id: ServiceId,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        duration_minutes: int | None = None,
    ) -> ServiceEntity:
        """
        Update service information.

        Args:
            service_id: Service identifier
            name: Service name (optional)
            description: Service description (optional)
            category: Service category (optional)
            duration_minutes: Service duration in minutes (optional)

        Returns:
            Updated ServiceEntity

        Raises:
            ValueError: If service not found
            DomainError: If update is invalid
        """
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id.value} not found")

        if name is not None:
            service.update_name(name)
        if description is not None:
            service.update_description(description)
        if category is not None:
            service.update_category(category)
        if duration_minutes is not None:
            service.update_duration(duration_minutes)

        await self.service_repository.save(service)

        return service


class UpdateServiceGroupSettingsUseCase:
    """Use case for updating service group settings."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(
        self,
        service_id: ServiceId,
        is_group_service: bool,
        max_participants: int | None = None,
    ) -> ServiceEntity:
        """
        Update service group settings.

        Args:
            service_id: Service identifier
            is_group_service: Whether this is a group service
            max_participants: Maximum participants for group services (optional)

        Returns:
            Updated ServiceEntity

        Raises:
            ValueError: If service not found
            DomainError: If update is invalid
        """
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id.value} not found")

        service.update_group_settings(is_group_service, max_participants)
        await self.service_repository.save(service)

        return service


class GetServiceUseCase:
    """Use case for retrieving a service."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(self, service_id: ServiceId) -> ServiceEntity | None:
        """
        Get service by ID.

        Args:
            service_id: Service identifier

        Returns:
            ServiceEntity if found, None otherwise
        """
        return await self.service_repository.get_by_id(service_id)

    async def execute_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ServiceEntity | None:
        """
        Get service by name within a tenant.

        Args:
            tenant_id: Tenant identifier
            name: Service name

        Returns:
            ServiceEntity if found, None otherwise
        """
        return await self.service_repository.get_by_name(tenant_id, name)
