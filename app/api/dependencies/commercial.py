"""Repository dependency factories for the commercial bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.contract_repository import ContractRepository
from app.infrastructure.repositories.contract_repository import ContractRepositoryImpl


async def get_contract_repository(
    db: AsyncSession = Depends(get_db),
) -> ContractRepository:
    """
    Dependency for getting contract repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ContractRepository implementation
    """
    return ContractRepositoryImpl(db)
