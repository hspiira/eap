"""
Tenant Repository Implementation

SQLAlchemy implementation of TenantRepository interface.
"""

from sqlalchemy.orm import Session
from app.domain.entities.tenant import TenantEntity
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantId
from app.infrastructure.mappers.tenant_mapper import TenantMapper
from app.infrastructure.models.tenant_model import TenantModel


class SQLAlchemyTenantRepository(TenantRepository):
    """
    SQLAlchemy implementation of TenantRepository.
    
    Handles data access for Tenant aggregate.
    Uses mapper to convert between entity and model.
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_by_id(self, tenant_id: TenantId) -> TenantEntity | None:
        """Get tenant by ID, excluding soft-deleted tenants."""
        model = self.session.query(TenantModel)\
            .filter(
                TenantModel.id == tenant_id.value,
                TenantModel.deleted_at.is_(None)
            )\
            .first()
        
        if not model:
            return None
        
        return TenantMapper.to_entity(model)
    
    def get_by_code(self, code: str) -> TenantEntity | None:
        """Get tenant by code, excluding soft-deleted tenants."""
        model = self.session.query(TenantModel)\
            .filter(
                TenantModel.code == code,
                TenantModel.deleted_at.is_(None)
            )\
            .first()
        
        if not model:
            return None
        
        return TenantMapper.to_entity(model)
    
    def save(self, tenant: TenantEntity) -> None:
        """
        Save tenant aggregate atomically.
        
        Uses merge to handle both insert and update.
        """
        model = TenantMapper.to_model(tenant)
        self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work
    
    def delete(self, tenant_id: TenantId) -> None:
        """
        Soft delete tenant.
        
        In practice, this is usually done by calling tenant.terminate()
        and then save(), but this method provides explicit soft delete.
        """
        model = self.session.query(TenantModel)\
            .filter(TenantModel.id == tenant_id.value)\
            .first()
        
        if model:
            from app.shared.utils.datetime import utc_now
            model.deleted_at = utc_now()
            self.session.merge(model)
    
    def exists(self, tenant_id: TenantId) -> bool:
        """Check if tenant exists (not soft-deleted)."""
        count = self.session.query(TenantModel)\
            .filter(
                TenantModel.id == tenant_id.value,
                TenantModel.deleted_at.is_(None)
            )\
            .count()
        
        return count > 0
