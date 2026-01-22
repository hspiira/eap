"""ClientTag Use Cases - Application services for ClientTag operations."""

from app.domain.entities.client_tag import ClientTagEntity
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.value_objects.core import ClientTagId, TenantId
from app.shared.utils.datetime import utc_now


class CreateClientTagUseCase:
    def __init__(self, tag_repository: ClientTagRepository):
        self.tag_repository = tag_repository

    async def execute(
        self,
        tag_id: ClientTagId,
        tenant_id: TenantId,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> ClientTagEntity:
        existing = await self.tag_repository.get_by_name(name, tenant_id)
        if existing:
            raise ValueError(f"Tag with name '{name}' already exists")

        tag = ClientTagEntity(
            _id=tag_id,
            _tenant_id=tenant_id,
            _name=name,
            _description=description,
            _color=color,
            _is_active=True,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        await self.tag_repository.save(tag)
        return tag


class UpdateClientTagUseCase:
    def __init__(self, tag_repository: ClientTagRepository):
        self.tag_repository = tag_repository

    async def execute(
        self,
        tag_id: ClientTagId,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
    ) -> ClientTagEntity:
        tag = await self.tag_repository.get_by_id(tag_id)
        if not tag:
            raise ValueError(f"Tag {tag_id.value} not found")

        if name and name != tag._name:
            existing = await self.tag_repository.get_by_name(name, tag._tenant_id)
            if existing:
                raise ValueError(f"Tag with name '{name}' already exists")

        if name:
            tag.update_name(name)
        if description is not None:
            tag.update_description(description)
        if color is not None:
            tag.update_color(color)

        await self.tag_repository.save(tag)
        return tag


class ActivateClientTagUseCase:
    def __init__(self, tag_repository: ClientTagRepository):
        self.tag_repository = tag_repository

    async def execute(self, tag_id: ClientTagId) -> ClientTagEntity:
        tag = await self.tag_repository.get_by_id(tag_id)
        if not tag:
            raise ValueError(f"Tag {tag_id.value} not found")
        tag.activate()
        await self.tag_repository.save(tag)
        return tag


class DeactivateClientTagUseCase:
    def __init__(self, tag_repository: ClientTagRepository):
        self.tag_repository = tag_repository

    async def execute(self, tag_id: ClientTagId) -> ClientTagEntity:
        tag = await self.tag_repository.get_by_id(tag_id)
        if not tag:
            raise ValueError(f"Tag {tag_id.value} not found")
        tag.deactivate()
        await self.tag_repository.save(tag)
        return tag


class GetClientTagUseCase:
    def __init__(self, tag_repository: ClientTagRepository):
        self.tag_repository = tag_repository

    async def execute(self, tag_id: ClientTagId) -> ClientTagEntity | None:
        return await self.tag_repository.get_by_id(tag_id)
