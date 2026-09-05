"""Repository dependency factories for the identity bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.repositories.contact_repository import ContactRepositoryImpl
from app.infrastructure.repositories.person_repository import PersonRepositoryImpl
from app.infrastructure.repositories.user_repository import UserRepositoryImpl


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """
    Dependency for getting user repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        UserRepository implementation
    """
    return UserRepositoryImpl(db)


async def get_person_repository(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
) -> PersonRepository:
    """
    Dependency for getting person repository.

    Args:
        db: Database session (injected by FastAPI)
        user_repo: User repository (injected dependency)

    Returns:
        PersonRepository implementation
    """
    return PersonRepositoryImpl(db, user_repo)


async def get_contact_repository(
    db: AsyncSession = Depends(get_db),
) -> ContactRepository:
    """
    Dependency for getting contact repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ContactRepository implementation
    """
    return ContactRepositoryImpl(db)
