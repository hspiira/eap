"""
KPI Use Cases

Application services for KPI aggregate operations.
Refactored to use base use case classes.
"""

from decimal import Decimal

from app.application.use_cases.base import (
    BaseUseCase,
    create_activate_use_case,
    create_deactivate_use_case,
)
from app.domain.entities.kpi import KPIEntity, KPIAssignmentEntity
from app.domain.enums import KPICategory, KPIMeasurementUnit
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.value_objects.core import KPIId, KPIAssignmentId, TenantId
from app.shared.utils.datetime import utc_now


# =============================================================================
# KPI LIFECYCLE USE CASES (Using Base Factories)
# =============================================================================


class ActivateKPIUseCase:
    """Use case for activating a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        self._use_case = create_activate_use_case(kpi_repository, "KPI")

    async def execute(self, kpi_id: KPIId) -> KPIEntity:
        return await self._use_case.execute(kpi_id)


class DeactivateKPIUseCase:
    """Use case for deactivating a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        self._use_case = create_deactivate_use_case(kpi_repository, "KPI")

    async def execute(self, kpi_id: KPIId) -> KPIEntity:
        return await self._use_case.execute(kpi_id)


# =============================================================================
# KPI CREATE USE CASE
# =============================================================================


class CreateKPIUseCase(BaseUseCase[KPIEntity, KPIId]):
    """Use case for creating a new KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        super().__init__(kpi_repository)
        self.kpi_repository = kpi_repository

    async def execute(
        self,
        kpi_id: KPIId,
        tenant_id: TenantId,
        name: str,
        category: KPICategory,
        measurement_unit: KPIMeasurementUnit,
        description: str | None = None,
        target_value: Decimal | None = None,
        threshold_min: Decimal | None = None,
        threshold_max: Decimal | None = None,
        formula: str | None = None,
    ) -> KPIEntity:
        """Create a new KPI."""
        # Check if KPI with same name already exists
        existing = await self.kpi_repository.get_by_name(name, tenant_id)
        if existing:
            raise ValueError(f"KPI with name '{name}' already exists")

        # Create KPI entity
        kpi = KPIEntity(
            id=kpi_id,
            tenant_id=tenant_id,
            name=name,
            category=category,
            measurement_unit=measurement_unit,
            description=description,
            target_value=target_value,
            threshold_min=threshold_min,
            threshold_max=threshold_max,
            formula=formula,
            _is_active=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        return await self._save_and_publish_events(kpi)


# =============================================================================
# KPI UPDATE USE CASE
# =============================================================================


class UpdateKPIUseCase(BaseUseCase[KPIEntity, KPIId]):
    """Use case for updating a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        super().__init__(kpi_repository)
        self.kpi_repository = kpi_repository

    async def execute(
        self,
        kpi_id: KPIId,
        name: str | None = None,
        description: str | None = None,
        target_value: Decimal | None = None,
        threshold_min: Decimal | None = None,
        threshold_max: Decimal | None = None,
        formula: str | None = None,
    ) -> KPIEntity:
        """Update a KPI."""
        kpi = await self._get_entity_or_raise(kpi_id, "KPI")

        # Check name uniqueness if name is being updated
        if name and name != kpi.name:
            existing = await self.kpi_repository.get_by_name(name, kpi.tenant_id)
            if existing:
                raise ValueError(f"KPI with name '{name}' already exists")

        kpi.update_definition(
            name=name,
            description=description,
            target_value=target_value,
            threshold_min=threshold_min,
            threshold_max=threshold_max,
            formula=formula,
        )

        return await self._save_and_publish_events(kpi)


# =============================================================================
# KPI QUERY USE CASE
# =============================================================================


class GetKPIUseCase(BaseUseCase[KPIEntity, KPIId]):
    """Use case for retrieving a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        super().__init__(kpi_repository)

    async def execute(self, kpi_id: KPIId) -> KPIEntity | None:
        """Get KPI by ID."""
        return await self.repository.get_by_id(kpi_id)


# =============================================================================
# KPI ASSIGNMENT LIFECYCLE USE CASES (Using Base Factories)
# =============================================================================


class ActivateKPIAssignmentUseCase:
    """Use case for activating a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        self._use_case = create_activate_use_case(assignment_repository, "Assignment")

    async def execute(self, assignment_id: KPIAssignmentId) -> KPIAssignmentEntity:
        return await self._use_case.execute(assignment_id)


class DeactivateKPIAssignmentUseCase:
    """Use case for deactivating a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        self._use_case = create_deactivate_use_case(assignment_repository, "Assignment")

    async def execute(self, assignment_id: KPIAssignmentId) -> KPIAssignmentEntity:
        return await self._use_case.execute(assignment_id)


# =============================================================================
# KPI ASSIGNMENT CREATE USE CASE
# =============================================================================


class CreateKPIAssignmentUseCase(BaseUseCase[KPIAssignmentEntity, KPIAssignmentId]):
    """Use case for creating a KPI assignment."""

    def __init__(
        self,
        kpi_repository: KPIRepository,
        assignment_repository: KPIAssignmentRepository,
    ):
        super().__init__(assignment_repository)
        self.kpi_repository = kpi_repository

    async def execute(
        self,
        assignment_id: KPIAssignmentId,
        kpi_id: KPIId,
        tenant_id: TenantId,
        client_id: str | None = None,
        contract_id: str | None = None,
        target_value: Decimal | None = None,
    ) -> KPIAssignmentEntity:
        """Create a new KPI assignment."""
        # Validate KPI exists
        kpi = await self.kpi_repository.get_by_id(kpi_id)
        if not kpi:
            raise ValueError(f"KPI {kpi_id.value} not found")

        # Validate either client or contract is provided
        if not client_id and not contract_id:
            raise ValueError("Either client_id or contract_id must be provided")
        if client_id and contract_id:
            raise ValueError("Cannot provide both client_id and contract_id")

        # Create assignment entity
        assignment = KPIAssignmentEntity(
            id=assignment_id,
            kpi_id=kpi_id,
            tenant_id=tenant_id,
            client_id=client_id,
            contract_id=contract_id,
            target_value=target_value,
            _is_active=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        return await self._save_and_publish_events(assignment)


# =============================================================================
# KPI ASSIGNMENT UPDATE USE CASE
# =============================================================================


class UpdateKPIAssignmentUseCase(BaseUseCase[KPIAssignmentEntity, KPIAssignmentId]):
    """Use case for updating a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        super().__init__(assignment_repository)

    async def execute(
        self, assignment_id: KPIAssignmentId, target_value: Decimal | None
    ) -> KPIAssignmentEntity:
        """Update a KPI assignment."""
        assignment = await self._get_entity_or_raise(assignment_id, "Assignment")
        assignment.update_target(target_value)
        return await self._save_and_publish_events(assignment)


# =============================================================================
# KPI ASSIGNMENT QUERY USE CASE
# =============================================================================


class GetKPIAssignmentUseCase(BaseUseCase[KPIAssignmentEntity, KPIAssignmentId]):
    """Use case for retrieving a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        super().__init__(assignment_repository)

    async def execute(self, assignment_id: KPIAssignmentId) -> KPIAssignmentEntity | None:
        """Get assignment by ID."""
        return await self.repository.get_by_id(assignment_id)
