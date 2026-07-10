"""ClientTag Use Cases - Application services for ClientTag operations."""

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.client_tag import ClientTagEntity
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.value_objects.core import ClientTagId, TenantId
from app.shared.utils.datetime import utc_now


# Lifecycle dispatched via TransitionUseCase + ClientTagTransition.


class CreateClientTagUseCase(BaseUseCase[ClientTagEntity, ClientTagId]):
    """Use case for creating a client tag."""

    def __init__(self, tag_repository: ClientTagRepository):
        super().__init__(tag_repository)
        self.tag_repository = tag_repository

    async def execute(
        self,
        tag_id: ClientTagId,
        tenant_id: TenantId,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> ClientTagEntity:
        """Create a new client tag."""
        existing = await self.tag_repository.get_by_name(name, tenant_id)
        if existing:
            raise ValueError(f"Tag with name '{name}' already exists")

        tag = ClientTagEntity(
            id=tag_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            color=color,
            _is_active=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        return await self._save_and_publish_events(tag)


# =============================================================================
# UPDATE USE CASE
# =============================================================================


class UpdateClientTagUseCase(BaseUseCase[ClientTagEntity, ClientTagId]):
    """Use case for updating a client tag."""

    def __init__(self, tag_repository: ClientTagRepository):
        super().__init__(tag_repository)
        self.tag_repository = tag_repository

    async def execute(
        self,
        tag_id: ClientTagId,
        tenant_id: TenantId,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
    ) -> ClientTagEntity:
        """Update a client tag."""
        tag = await self._get_entity_or_raise(tag_id, "Tag")
        if not tag:
            raise ValueError(f"Tag {tag_id.value} not found")
        if tag.tenant_id != tenant_id:
            raise ValueError("Tag not found")

        if name and name != tag.name:
            existing = await self.tag_repository.get_by_name(name, tag.tenant_id)
            if existing:
                raise ValueError(f"Tag with name '{name}' already exists")

        if name:
            tag.update_name(name)
        if description is not None:
            tag.update_description(description)
        if color is not None:
            tag.update_color(color)

        return await self._save_and_publish_events(tag)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetClientTagUseCase(BaseUseCase[ClientTagEntity, ClientTagId]):
    """Use case for retrieving a client tag."""

    def __init__(self, tag_repository: ClientTagRepository):
        super().__init__(tag_repository)

    async def execute(self, tag_id: ClientTagId) -> ClientTagEntity | None:
        """Get client tag by ID."""
        return await self.repository.get_by_id(tag_id)
