"""
Repository Interfaces

Repository interfaces are defined in the domain layer.
Implementations live in the infrastructure layer.
"""

from app.domain.repositories.tenant_repository import TenantRepository

__all__ = [
    "TenantRepository",
]
