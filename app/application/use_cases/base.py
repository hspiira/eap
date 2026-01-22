"""
Base Use Case Classes

Generic base classes that eliminate repetitive use case patterns.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Protocol, Any

from app.domain.events import DomainEvent
from app.shared.events.event_bus import event_bus
from app.shared.utils.datetime import utc_now

# Type variables for generic use cases
TEntity = TypeVar("TEntity")
TId = TypeVar("TId")
TRepository = TypeVar("TRepository")


class RepositoryProtocol(Protocol[TEntity, TId]):
    """Protocol defining required repository methods."""
    
    async def get_by_id(self, entity_id: TId) -> TEntity | None: ...
    async def save(self, entity: TEntity) -> None: ...


class BaseUseCase(ABC, Generic[TEntity, TId]):
    """
    Abstract base class for use cases.
    
    Provides common functionality:
    - Repository injection
    - Entity fetching with not-found handling
    - Event publishing
    """
    
    def __init__(self, repository: RepositoryProtocol[TEntity, TId]):
        self.repository = repository
    
    async def _get_entity_or_raise(self, entity_id: TId, entity_name: str = "Entity") -> TEntity:
        """
        Get entity by ID or raise ValueError if not found.
        
        Args:
            entity_id: The entity identifier
            entity_name: Name for error message (e.g., "User", "Client")
            
        Returns:
            The entity
            
        Raises:
            ValueError: If entity not found
        """
        entity = await self.repository.get_by_id(entity_id)
        if not entity:
            id_value = getattr(entity_id, 'value', str(entity_id))
            raise ValueError(f"{entity_name} {id_value} not found")
        return entity
    
    async def _save_and_publish_events(self, entity: TEntity) -> TEntity:
        """
        Save entity and publish any collected domain events.
        
        Args:
            entity: The entity to save
            
        Returns:
            The saved entity
        """
        await self.repository.save(entity)
        
        # Publish domain events if entity has them
        if hasattr(entity, '_events'):
            events: list[DomainEvent] = getattr(entity, '_events', [])
            for event in events:
                await event_bus.publish(event)
            # Clear events after publishing
            events.clear()
        
        return entity


class EntityLifecycleUseCase(BaseUseCase[TEntity, TId]):
    """
    Base class for entity lifecycle operations (activate, suspend, etc.).
    
    Subclasses only need to define:
    - entity_name: For error messages
    - _perform_action: The actual domain operation
    """
    
    entity_name: str = "Entity"
    
    @abstractmethod
    async def _perform_action(self, entity: TEntity, *args: Any, **kwargs: Any) -> None:
        """Perform the domain action on the entity."""
        pass
    
    async def execute(self, entity_id: TId, *args: Any, **kwargs: Any) -> TEntity:
        """
        Execute the lifecycle operation.
        
        Args:
            entity_id: The entity identifier
            *args, **kwargs: Additional arguments for the action
            
        Returns:
            The modified entity
        """
        entity = await self._get_entity_or_raise(entity_id, self.entity_name)
        await self._perform_action(entity, *args, **kwargs)
        
        # Update timestamp if entity has _updated_at
        if hasattr(entity, '_updated_at'):
            setattr(entity, '_updated_at', utc_now())
        
        return await self._save_and_publish_events(entity)


# =============================================================================
# CONCRETE GENERIC USE CASES
# =============================================================================


class ActivateUseCase(EntityLifecycleUseCase[TEntity, TId]):
    """Generic activate use case."""
    
    async def _perform_action(self, entity: TEntity, *args: Any, **kwargs: Any) -> None:
        if hasattr(entity, 'activate'):
            entity.activate()
        else:
            raise NotImplementedError(f"{self.entity_name} does not support activation")


class DeactivateUseCase(EntityLifecycleUseCase[TEntity, TId]):
    """Generic deactivate use case."""
    
    async def _perform_action(self, entity: TEntity, reason: str | None = None, **kwargs: Any) -> None:
        if hasattr(entity, 'deactivate'):
            entity.deactivate(reason)
        else:
            raise NotImplementedError(f"{self.entity_name} does not support deactivation")


class SuspendUseCase(EntityLifecycleUseCase[TEntity, TId]):
    """Generic suspend use case."""
    
    async def _perform_action(self, entity: TEntity, reason: str, **kwargs: Any) -> None:
        if hasattr(entity, 'suspend'):
            entity.suspend(reason)
        else:
            raise NotImplementedError(f"{self.entity_name} does not support suspension")


class TerminateUseCase(EntityLifecycleUseCase[TEntity, TId]):
    """Generic terminate use case."""
    
    async def _perform_action(self, entity: TEntity, reason: str, **kwargs: Any) -> None:
        if hasattr(entity, 'terminate'):
            entity.terminate(reason)
        else:
            raise NotImplementedError(f"{self.entity_name} does not support termination")


class ArchiveUseCase(EntityLifecycleUseCase[TEntity, TId]):
    """Generic archive use case."""
    
    async def _perform_action(self, entity: TEntity, *args: Any, **kwargs: Any) -> None:
        if hasattr(entity, 'archive'):
            entity.archive()
        else:
            raise NotImplementedError(f"{self.entity_name} does not support archiving")


class RestoreUseCase(EntityLifecycleUseCase[TEntity, TId]):
    """Generic restore use case."""
    
    async def _perform_action(self, entity: TEntity, *args: Any, **kwargs: Any) -> None:
        if hasattr(entity, 'restore'):
            entity.restore()
        else:
            raise NotImplementedError(f"{self.entity_name} does not support restoration")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_activate_use_case(
    repository: RepositoryProtocol[TEntity, TId],
    entity_name: str,
) -> ActivateUseCase[TEntity, TId]:
    """Factory to create an activate use case with custom entity name."""
    use_case = ActivateUseCase(repository)
    use_case.entity_name = entity_name
    return use_case


def create_deactivate_use_case(
    repository: RepositoryProtocol[TEntity, TId],
    entity_name: str,
) -> DeactivateUseCase[TEntity, TId]:
    """Factory to create a deactivate use case with custom entity name."""
    use_case = DeactivateUseCase(repository)
    use_case.entity_name = entity_name
    return use_case


def create_suspend_use_case(
    repository: RepositoryProtocol[TEntity, TId],
    entity_name: str,
) -> SuspendUseCase[TEntity, TId]:
    """Factory to create a suspend use case with custom entity name."""
    use_case = SuspendUseCase(repository)
    use_case.entity_name = entity_name
    return use_case


def create_terminate_use_case(
    repository: RepositoryProtocol[TEntity, TId],
    entity_name: str,
) -> TerminateUseCase[TEntity, TId]:
    """Factory to create a terminate use case with custom entity name."""
    use_case = TerminateUseCase(repository)
    use_case.entity_name = entity_name
    return use_case


def create_archive_use_case(
    repository: RepositoryProtocol[TEntity, TId],
    entity_name: str,
) -> ArchiveUseCase[TEntity, TId]:
    """Factory to create an archive use case with custom entity name."""
    use_case = ArchiveUseCase(repository)
    use_case.entity_name = entity_name
    return use_case


def create_restore_use_case(
    repository: RepositoryProtocol[TEntity, TId],
    entity_name: str,
) -> RestoreUseCase[TEntity, TId]:
    """Factory to create a restore use case with custom entity name."""
    use_case = RestoreUseCase(repository)
    use_case.entity_name = entity_name
    return use_case
