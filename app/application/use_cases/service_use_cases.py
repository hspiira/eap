"""
Service Use Cases

Application services for Service aggregate operations.
Refactored to use base use case classes.
"""

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.service import ServiceEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.value_objects.core import ServiceId, TenantId
from app.shared.utils.datetime import utc_now

# Lifecycle dispatched via TransitionUseCase + ServiceTransition.


class CreateServiceUseCase(BaseUseCase[ServiceEntity, ServiceId]):
    """Use case for creating a new service."""

    def __init__(self, service_repository: ServiceRepository):
        super().__init__(service_repository)
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
        """Create a new service."""
        # Check if service already exists
        existing = await self.service_repository.get_by_name(tenant_id, name)
        if existing:
            raise ValueError(f"Service with name '{name}' already exists")

        # Create service entity
        now = utc_now()
        service = ServiceEntity(
            id=service_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            status=BaseStatus.PENDING,
            created_at=now,
            updated_at=now,
            category=category,
            duration_minutes=duration_minutes,
            is_group_service=is_group_service,
            max_participants=max_participants,
        )

        return await self._save_and_publish_events(service)


# =============================================================================
# UPDATE USE CASES
# =============================================================================


class UpdateServiceUseCase(BaseUseCase[ServiceEntity, ServiceId]):
    """Use case for updating service information."""

    def __init__(self, service_repository: ServiceRepository):
        super().__init__(service_repository)

    async def execute(
        self,
        service_id: ServiceId,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        duration_minutes: int | None = None,
    ) -> ServiceEntity:
        """Update service information."""
        service = await self._get_entity_or_raise(service_id, "Service")

        if name is not None:
            service.update_name(name)
        if description is not None:
            service.update_description(description)
        if category is not None:
            service.update_category(category)
        if duration_minutes is not None:
            service.update_duration(duration_minutes)

        return await self._save_and_publish_events(service)


class UpdateServiceGroupSettingsUseCase(BaseUseCase[ServiceEntity, ServiceId]):
    """Use case for updating service group settings."""

    def __init__(self, service_repository: ServiceRepository):
        super().__init__(service_repository)

    async def execute(
        self,
        service_id: ServiceId,
        is_group_service: bool,
        max_participants: int | None = None,
    ) -> ServiceEntity:
        """Update service group settings."""
        service = await self._get_entity_or_raise(service_id, "Service")
        service.update_group_settings(
            is_group_service=is_group_service, max_participants=max_participants
        )
        return await self._save_and_publish_events(service)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetServiceUseCase(BaseUseCase[ServiceEntity, ServiceId]):
    """Use case for retrieving a service."""

    def __init__(self, service_repository: ServiceRepository):
        super().__init__(service_repository)
        self.service_repository = service_repository

    async def execute(self, service_id: ServiceId) -> ServiceEntity | None:
        """Get service by ID."""
        return await self.repository.get_by_id(service_id)

    async def execute_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ServiceEntity | None:
        """Get service by name within a tenant."""
        return await self.service_repository.get_by_name(tenant_id, name)
