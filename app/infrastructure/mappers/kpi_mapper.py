"""
KPI Mapper

Converts between KPI entities (domain) and models (persistence).
"""

from app.domain.entities.kpi import KPIAssignmentEntity, KPIEntity
from app.domain.value_objects.core import KPIAssignmentId, KPIId, TenantId
from app.infrastructure.models.kpi_model import KPIAssignmentModel, KPIModel
from app.shared.utils.datetime import ensure_utc


class KPIMapper:
    """Mapper for KPIEntity ↔ KPIModel conversion"""

    @staticmethod
    def to_entity(model: KPIModel) -> KPIEntity:
        """
        Convert database model to domain entity.

        Args:
            model: KPIModel from database

        Returns:
            KPIEntity with business logic
        """

        kpi_id = KPIId(model.id)
        tenant_id = TenantId(model.tenant_id)

        return KPIEntity(
            id=kpi_id,
            tenant_id=tenant_id,
            name=model.name,
            description=model.description,
            category=model.category,
            measurement_unit=model.measurement_unit,
            target_value=model.target_value if model.target_value else None,
            threshold_min=model.threshold_min if model.threshold_min else None,
            threshold_max=model.threshold_max if model.threshold_max else None,
            formula=model.formula,
            _is_active=model.is_active,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: KPIEntity) -> KPIModel:
        """
        Convert domain entity to database model.

        Args:
            entity: KPIEntity from domain

        Returns:
            KPIModel for persistence
        """
        model = KPIModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            name=entity.name,
            description=entity.description,
            category=entity.category,
            measurement_unit=entity.measurement_unit,
            target_value=entity.target_value if entity.target_value else None,
            threshold_min=entity.threshold_min if entity.threshold_min else None,
            threshold_max=entity.threshold_max if entity.threshold_max else None,
            formula=entity.formula,
            is_active=entity._is_active,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )

        return model


class KPIAssignmentMapper:
    """Mapper for KPIAssignmentEntity ↔ KPIAssignmentModel conversion"""

    @staticmethod
    def to_entity(model: KPIAssignmentModel) -> KPIAssignmentEntity:
        """
        Convert database model to domain entity.

        Args:
            model: KPIAssignmentModel from database

        Returns:
            KPIAssignmentEntity with business logic
        """
        assignment_id = KPIAssignmentId(model.id)
        kpi_id = KPIId(model.kpi_id)
        tenant_id = TenantId(model.tenant_id)

        return KPIAssignmentEntity(
            id=assignment_id,
            kpi_id=kpi_id,
            tenant_id=tenant_id,
            client_id=model.client_id,
            contract_id=model.contract_id,
            target_value=model.target_value if model.target_value else None,
            _is_active=model.is_active,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: KPIAssignmentEntity) -> KPIAssignmentModel:
        """
        Convert domain entity to database model.

        Args:
            entity: KPIAssignmentEntity from domain

        Returns:
            KPIAssignmentModel for persistence
        """
        model = KPIAssignmentModel(
            id=entity.id.value,
            kpi_id=entity.kpi_id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id,
            contract_id=entity.contract_id,
            target_value=entity.target_value if entity.target_value else None,
            is_active=entity._is_active,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )

        return model
