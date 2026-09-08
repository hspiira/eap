"""Repository dependency factories for the delivery bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.document_type_repository import DocumentTypeRepository
from app.domain.repositories.kpi_category_repository import KPICategoryRepository
from app.domain.repositories.kpi_measurement_unit_repository import (
    KPIMeasurementUnitRepository,
)
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.repositories.service_assignment_repository import (
    ServiceAssignmentRepository,
)
from app.domain.repositories.service_category_repository import (
    ServiceCategoryRepository,
)
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.repositories.service_session_repository import (
    ServiceSessionRepository,
)
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl
from app.infrastructure.repositories.kpi_repository import (
    KPIAssignmentRepositoryImpl,
    KPIRepositoryImpl,
)
from app.infrastructure.repositories.service_assignment_repository import (
    ServiceAssignmentRepositoryImpl,
)
from app.infrastructure.repositories.service_repository import ServiceRepositoryImpl
from app.infrastructure.repositories.service_session_repository import (
    ServiceSessionRepositoryImpl,
)


async def get_service_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceRepository:
    """
    Dependency for getting service repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceRepository implementation
    """
    return ServiceRepositoryImpl(db)


async def get_service_session_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceSessionRepository:
    """
    Dependency for getting service session repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceSessionRepository implementation
    """
    return ServiceSessionRepositoryImpl(db)


async def get_document_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    """
    Dependency for getting document repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        DocumentRepository implementation
    """
    return DocumentRepositoryImpl(db)


async def get_document_type_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentTypeRepository:
    from app.infrastructure.repositories.document_type_repository import (
        DocumentTypeRepositoryImpl,
    )

    return DocumentTypeRepositoryImpl(db)


async def get_kpi_repository(
    db: AsyncSession = Depends(get_db),
) -> KPIRepository:
    """
    Dependency for getting KPI repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        KPIRepository implementation
    """
    return KPIRepositoryImpl(db)


async def get_kpi_category_repository(
    db: AsyncSession = Depends(get_db),
) -> KPICategoryRepository:
    from app.infrastructure.repositories.kpi_category_repository import (
        KPICategoryRepositoryImpl,
    )

    return KPICategoryRepositoryImpl(db)


async def get_kpi_measurement_unit_repository(
    db: AsyncSession = Depends(get_db),
) -> KPIMeasurementUnitRepository:
    from app.infrastructure.repositories.kpi_measurement_unit_repository import (
        KPIMeasurementUnitRepositoryImpl,
    )

    return KPIMeasurementUnitRepositoryImpl(db)


async def get_kpi_assignment_repository(
    db: AsyncSession = Depends(get_db),
) -> KPIAssignmentRepository:
    """
    Dependency for getting KPI assignment repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        KPIAssignmentRepository implementation
    """
    return KPIAssignmentRepositoryImpl(db)


async def get_service_assignment_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceAssignmentRepository:
    """
    Dependency for getting service assignment repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceAssignmentRepository implementation
    """
    return ServiceAssignmentRepositoryImpl(db)


async def get_diagnosis_repository(
    db: AsyncSession = Depends(get_db),
) -> "DiagnosisRepository":
    from app.infrastructure.repositories.diagnosis_repository import (
        DiagnosisRepositoryImpl,
    )

    return DiagnosisRepositoryImpl(db)


async def get_service_category_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceCategoryRepository:
    from app.infrastructure.repositories.service_category_repository import (
        ServiceCategoryRepositoryImpl,
    )

    return ServiceCategoryRepositoryImpl(db)
