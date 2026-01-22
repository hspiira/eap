"""
KPI Use Cases

Application services for KPI aggregate operations.
"""

from decimal import Decimal

from app.domain.entities.kpi import KPIEntity, KPIAssignmentEntity
from app.domain.enums import KPICategory, KPIMeasurementUnit
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.value_objects.core import KPIId, KPIAssignmentId, TenantId
from app.shared.utils.datetime import utc_now


class CreateKPIUseCase:
    """Use case for creating a new KPI."""

    def __init__(self, kpi_repository: KPIRepository):
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
        """
        Create a new KPI.

        Args:
            kpi_id: Unique KPI identifier
            tenant_id: Tenant identifier
            name: KPI name
            category: KPI category
            measurement_unit: Measurement unit
            description: KPI description (optional)
            target_value: Target value (optional)
            threshold_min: Minimum threshold (optional)
            threshold_max: Maximum threshold (optional)
            formula: Calculation formula (optional)

        Returns:
            Created KPIEntity

        Raises:
            ValueError: If validation fails
        """
        # Check if KPI with same name already exists
        existing = await self.kpi_repository.get_by_name(name, tenant_id)
        if existing:
            raise ValueError(f"KPI with name '{name}' already exists")

        # Create KPI entity
        kpi = KPIEntity(
            _id=kpi_id,
            _tenant_id=tenant_id,
            _name=name,
            _category=category,
            _measurement_unit=measurement_unit,
            _description=description,
            _target_value=target_value,
            _threshold_min=threshold_min,
            _threshold_max=threshold_max,
            _formula=formula,
            _is_active=True,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        # Save KPI
        await self.kpi_repository.save(kpi)

        return kpi


class UpdateKPIUseCase:
    """Use case for updating a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
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
        """
        Update a KPI.

        Args:
            kpi_id: KPI identifier
            name: KPI name (optional)
            description: KPI description (optional)
            target_value: Target value (optional)
            threshold_min: Minimum threshold (optional)
            threshold_max: Maximum threshold (optional)
            formula: Calculation formula (optional)

        Returns:
            Updated KPIEntity

        Raises:
            ValueError: If KPI not found
            DomainError: If update is invalid
        """
        kpi = await self.kpi_repository.get_by_id(kpi_id)
        if not kpi:
            raise ValueError(f"KPI {kpi_id.value} not found")

        # Check name uniqueness if name is being updated
        if name and name != kpi._name:
            existing = await self.kpi_repository.get_by_name(name, kpi._tenant_id)
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
        await self.kpi_repository.save(kpi)

        return kpi


class ActivateKPIUseCase:
    """Use case for activating a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        self.kpi_repository = kpi_repository

    async def execute(self, kpi_id: KPIId) -> KPIEntity:
        """
        Activate a KPI.

        Args:
            kpi_id: KPI identifier

        Returns:
            Activated KPIEntity

        Raises:
            ValueError: If KPI not found
            DomainError: If activation is invalid
        """
        kpi = await self.kpi_repository.get_by_id(kpi_id)
        if not kpi:
            raise ValueError(f"KPI {kpi_id.value} not found")

        kpi.activate()
        await self.kpi_repository.save(kpi)

        return kpi


class DeactivateKPIUseCase:
    """Use case for deactivating a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        self.kpi_repository = kpi_repository

    async def execute(self, kpi_id: KPIId) -> KPIEntity:
        """
        Deactivate a KPI.

        Args:
            kpi_id: KPI identifier

        Returns:
            Deactivated KPIEntity

        Raises:
            ValueError: If KPI not found
            DomainError: If deactivation is invalid
        """
        kpi = await self.kpi_repository.get_by_id(kpi_id)
        if not kpi:
            raise ValueError(f"KPI {kpi_id.value} not found")

        kpi.deactivate()
        await self.kpi_repository.save(kpi)

        return kpi


class GetKPIUseCase:
    """Use case for retrieving a KPI."""

    def __init__(self, kpi_repository: KPIRepository):
        self.kpi_repository = kpi_repository

    async def execute(self, kpi_id: KPIId) -> KPIEntity | None:
        """
        Get KPI by ID.

        Args:
            kpi_id: KPI identifier

        Returns:
            KPIEntity if found, None otherwise
        """
        return await self.kpi_repository.get_by_id(kpi_id)


class CreateKPIAssignmentUseCase:
    """Use case for creating a KPI assignment."""

    def __init__(
        self,
        kpi_repository: KPIRepository,
        assignment_repository: KPIAssignmentRepository,
    ):
        self.kpi_repository = kpi_repository
        self.assignment_repository = assignment_repository

    async def execute(
        self,
        assignment_id: KPIAssignmentId,
        kpi_id: KPIId,
        tenant_id: TenantId,
        client_id: str | None = None,
        contract_id: str | None = None,
        target_value: Decimal | None = None,
    ) -> KPIAssignmentEntity:
        """
        Create a new KPI assignment.

        Args:
            assignment_id: Unique assignment identifier
            kpi_id: KPI identifier
            tenant_id: Tenant identifier
            client_id: Client identifier (optional)
            contract_id: Contract identifier (optional)
            target_value: Assignment-specific target value (optional)

        Returns:
            Created KPIAssignmentEntity

        Raises:
            ValueError: If validation fails
        """
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
            _id=assignment_id,
            _kpi_id=kpi_id,
            _tenant_id=tenant_id,
            _client_id=client_id,
            _contract_id=contract_id,
            _target_value=target_value,
            _is_active=True,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        # Save assignment
        await self.assignment_repository.save(assignment)

        return assignment


class UpdateKPIAssignmentUseCase:
    """Use case for updating a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(
        self, assignment_id: KPIAssignmentId, target_value: Decimal | None
    ) -> KPIAssignmentEntity:
        """
        Update a KPI assignment.

        Args:
            assignment_id: Assignment identifier
            target_value: Assignment-specific target value (optional)

        Returns:
            Updated KPIAssignmentEntity

        Raises:
            ValueError: If assignment not found
            DomainError: If update is invalid
        """
        assignment = await self.assignment_repository.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id.value} not found")

        assignment.update_target(target_value)
        await self.assignment_repository.save(assignment)

        return assignment


class ActivateKPIAssignmentUseCase:
    """Use case for activating a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(
        self, assignment_id: KPIAssignmentId
    ) -> KPIAssignmentEntity:
        """
        Activate a KPI assignment.

        Args:
            assignment_id: Assignment identifier

        Returns:
            Activated KPIAssignmentEntity

        Raises:
            ValueError: If assignment not found
            DomainError: If activation is invalid
        """
        assignment = await self.assignment_repository.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id.value} not found")

        assignment.activate()
        await self.assignment_repository.save(assignment)

        return assignment


class DeactivateKPIAssignmentUseCase:
    """Use case for deactivating a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(
        self, assignment_id: KPIAssignmentId
    ) -> KPIAssignmentEntity:
        """
        Deactivate a KPI assignment.

        Args:
            assignment_id: Assignment identifier

        Returns:
            Deactivated KPIAssignmentEntity

        Raises:
            ValueError: If assignment not found
            DomainError: If deactivation is invalid
        """
        assignment = await self.assignment_repository.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id.value} not found")

        assignment.deactivate()
        await self.assignment_repository.save(assignment)

        return assignment


class GetKPIAssignmentUseCase:
    """Use case for retrieving a KPI assignment."""

    def __init__(self, assignment_repository: KPIAssignmentRepository):
        self.assignment_repository = assignment_repository

    async def execute(
        self, assignment_id: KPIAssignmentId
    ) -> KPIAssignmentEntity | None:
        """
        Get assignment by ID.

        Args:
            assignment_id: Assignment identifier

        Returns:
            KPIAssignmentEntity if found, None otherwise
        """
        return await self.assignment_repository.get_by_id(assignment_id)
