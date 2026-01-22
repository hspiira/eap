"""
Repository Interfaces

Repository interfaces are defined in the domain layer.
Implementations live in the infrastructure layer.
"""

from app.domain.repositories.base_repository import BaseRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "ClientRepository",
    "ContractRepository",
    "PersonRepository",
    "TenantRepository",
    "UserRepository",
]
