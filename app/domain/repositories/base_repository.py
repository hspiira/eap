"""
Base Repository Interface

Generic repository interface with common CRUD operations.
Specific repositories extend this with domain-specific methods.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for generic repository
EntityType = TypeVar("EntityType")
IdType = TypeVar("IdType")


class BaseRepository(ABC, Generic[EntityType, IdType]):
    """
    Base repository interface with common CRUD operations.

    All repository interfaces should extend this base class.
    Provides standard methods: get_by_id, save, delete, exists.
    All methods are async.
    """

    @abstractmethod
    async def get_by_id(self, entity_id: IdType) -> EntityType | None:
        """
        Get entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """

    @abstractmethod
    async def save(self, entity: EntityType) -> None:
        """
        Save entity aggregate.

        This should save the entire aggregate atomically.
        Domain events are handled separately by the application service.

        Args:
            entity: Entity to save
        """

    @abstractmethod
    async def delete(self, entity_id: IdType) -> None:
        """
        Soft delete entity.

        Args:
            entity_id: Entity identifier
        """

    @abstractmethod
    async def exists(self, entity_id: IdType) -> bool:
        """
        Check if entity exists.

        Args:
            entity_id: Entity identifier

        Returns:
            True if entity exists, False otherwise
        """
