"""Base use case class with shared repository + event-publishing helpers.

Lifecycle dispatch is handled by ``TransitionUseCase`` in ``transitions.py``;
this module keeps only the abstractions that bespoke (non-transition) use
cases share — entity loading and event publishing.
"""

from abc import ABC
from typing import Generic, Protocol, TypeVar

from app.domain.events import DomainEvent
from app.shared.events.event_bus import event_bus

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


class RepositoryProtocol(Protocol[TEntity, TId]):
    async def get_by_id(self, entity_id: TId) -> TEntity | None: ...
    async def save(self, entity: TEntity) -> None: ...


class BaseUseCase(ABC, Generic[TEntity, TId]):
    """Common load + save + event-publish behaviour."""

    def __init__(self, repository: RepositoryProtocol[TEntity, TId]):
        self.repository = repository

    async def _get_entity_or_raise(
        self, entity_id: TId, entity_name: str = "Entity"
    ) -> TEntity:
        entity = await self.repository.get_by_id(entity_id)
        if not entity:
            id_value = getattr(entity_id, "value", str(entity_id))
            raise ValueError(f"{entity_name} {id_value} not found")
        return entity

    async def _save_and_publish_events(self, entity: TEntity) -> TEntity:
        """Save the entity and publish its collected domain events."""
        await self.repository.save(entity)
        events: list[DomainEvent] = getattr(entity, "events", []) or []
        for event in events:
            await event_bus.publish(event)
        return entity
