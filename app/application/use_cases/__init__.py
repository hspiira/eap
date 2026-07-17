"""
Use Cases

Application services that orchestrate domain logic.
"""

from app.application.use_cases.client_use_cases import (
    CreateClientUseCase,
    GetClientUseCase,
)
from app.application.use_cases.contract_use_cases import (
    CreateContractUseCase,
    GetContractUseCase,
)
from app.application.use_cases.person_use_cases import (
    CreateClientEmployeeUseCase,
    CreateDependentUseCase,
    GetPersonsByTypeUseCase,
    GetPersonUseCase,
)
from app.application.use_cases.tenant_use_cases import CreateTenantUseCase
from app.application.use_cases.transitions import (  # noqa: E402
    ClientTagTransition,
    ClientTransition,
    ContactTransition,
    ContractTransition,
    DocumentTransition,
    IndustryTransition,
    KPIAssignmentTransition,
    KPITransition,
    PersonTransition,
    ServiceAssignmentTransition,
    ServiceSessionTransition,
    ServiceTransition,
    TenantTransition,
    TransitionUseCase,
    UserTransition,  # noqa: E402
)
from app.application.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
)

__all__ = [
    "ClientTagTransition",
    "ClientTransition",
    "ContactTransition",
    "ContractTransition",
    "CreateClientUseCase",
    "CreateClientEmployeeUseCase",
    "CreateContractUseCase",
    "CreateDependentUseCase",
    "CreateTenantUseCase",
    "CreateUserUseCase",
    "DocumentTransition",
    "GetClientUseCase",
    "GetContractUseCase",
    "GetPersonUseCase",
    "GetPersonsByTypeUseCase",
    "GetUserUseCase",
    "IndustryTransition",
    "KPIAssignmentTransition",
    "KPITransition",
    "PersonTransition",
    "ServiceAssignmentTransition",
    "ServiceSessionTransition",
    "ServiceTransition",
    "TenantTransition",
    "TransitionUseCase",
    "UserTransition",
]
