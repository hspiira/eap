"""
KPI Mapper

Converts between KPI entities (domain) and models (persistence).
"""

from app.domain.entities.kpi import KPIEntity, KPIAssignmentEntity
from app.domain.enums import KPICategory, KPIMeasurementUnit
from app.domain.value_objects.core import KPIId, KPIAssignmentId, TenantId
from app.infrastructure.models.kpi_model import KPIAssignmentModel, KPIModel
from app.shared.utils.datetime import ensure_utc, utc_now


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
        from decimal import Decimal

        kpi_id = KPIId(model.id)
        tenant_id = TenantId(model.tenant_id)

        return KPIEntity(
            _id=kpi_id,
            _tenant_id=tenant_id,
            _name=model.name,
            _description=model.description,
            _category=model.category,
            _measurement_unit=model.measurement_unit,
            _target_value=model.target_value if model.target_value else None,
            _threshold_min=model.threshold_min if model.threshold_min else None,
            _threshold_max=model.threshold_max if model.threshold_max else None,
            _formula=model.formula,
            _is_active=model.is_active,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
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
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            name=entity._name,
            description=entity._description,
            category=entity._category,
            measurement_unit=entity._measurement_unit,
            target_value=entity._target_value if entity._target_value else None,
            threshold_min=entity._threshold_min if entity._threshold_min else None,
            threshold_max=entity._threshold_max if entity._threshold_max else None,
            formula=entity._formula,
            is_active=entity._is_active,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
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
            _id=assignment_id,
            _kpi_id=kpi_id,
            _tenant_id=tenant_id,
            _client_id=model.client_id,
            _contract_id=model.contract_id,
            _target_value=model.target_value if model.target_value else None,
            _is_active=model.is_active,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
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
            id=entity._id.value,
            kpi_id=entity._kpi_id.value,
            tenant_id=entity._tenant_id.value,
            client_id=entity._client_id,
            contract_id=entity._contract_id,
            target_value=entity._target_value if entity._target_value else None,
            is_active=entity._is_active,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )

        return model
