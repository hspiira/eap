"""
Cross-Entity Validation Service

Provides validation that spans multiple entities/aggregates.
This handles business rules that can't be enforced within a single entity.
"""

from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import BaseStatus
from app.domain.exceptions import ValidationException
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    PersonId,
    ServiceId,
    TenantId,
    UserId,
)


# =============================================================================
# REPOSITORY PROTOCOLS
# =============================================================================


class TenantRepositoryProtocol(Protocol):
    """Protocol for tenant repository."""
    async def get_by_id(self, tenant_id: TenantId): ...
    async def exists(self, tenant_id: TenantId) -> bool: ...


class ClientRepositoryProtocol(Protocol):
    """Protocol for client repository."""
    async def get_by_id(self, client_id: ClientId): ...
    async def exists(self, client_id: ClientId) -> bool: ...


class ContractRepositoryProtocol(Protocol):
    """Protocol for contract repository."""
    async def get_by_id(self, contract_id: ContractId): ...
    async def get_active_by_client(self, client_id: ClientId): ...


class PersonRepositoryProtocol(Protocol):
    """Protocol for person repository."""
    async def get_by_id(self, person_id: PersonId): ...
    async def exists(self, person_id: PersonId) -> bool: ...


class ServiceRepositoryProtocol(Protocol):
    """Protocol for service repository."""
    async def get_by_id(self, service_id: ServiceId): ...
    async def exists(self, service_id: ServiceId) -> bool: ...


class UserRepositoryProtocol(Protocol):
    """Protocol for user repository."""
    async def get_by_id(self, user_id: UserId): ...
    async def exists(self, user_id: UserId) -> bool: ...


# =============================================================================
# VALIDATION RESULT
# =============================================================================


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    errors: list[str]

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, errors=[])

    @classmethod
    def failure(cls, *errors: str) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(is_valid=False, errors=list(errors))

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge two validation results."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
        )

    def raise_if_invalid(self) -> None:
        """Raise ValidationException if validation failed."""
        if not self.is_valid:
            raise ValidationException(
                message="; ".join(self.errors),
                field=None,
            )


# =============================================================================
# VALIDATION SERVICE
# =============================================================================


class ValidationService:
    """
    Service for cross-entity validation.
    
    This service validates business rules that span multiple aggregates,
    such as ensuring referenced entities exist and are in valid states.
    """

    def __init__(
        self,
        tenant_repo: TenantRepositoryProtocol | None = None,
        client_repo: ClientRepositoryProtocol | None = None,
        contract_repo: ContractRepositoryProtocol | None = None,
        person_repo: PersonRepositoryProtocol | None = None,
        service_repo: ServiceRepositoryProtocol | None = None,
        user_repo: UserRepositoryProtocol | None = None,
    ):
        self._tenant_repo = tenant_repo
        self._client_repo = client_repo
        self._contract_repo = contract_repo
        self._person_repo = person_repo
        self._service_repo = service_repo
        self._user_repo = user_repo

    # =========================================================================
    # TENANT VALIDATION
    # =========================================================================

    async def validate_tenant_exists(self, tenant_id: TenantId) -> ValidationResult:
        """Validate that a tenant exists."""
        if not self._tenant_repo:
            return ValidationResult.success()

        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return ValidationResult.failure(
                f"Tenant {tenant_id.value} does not exist"
            )
        return ValidationResult.success()

    async def validate_tenant_active(self, tenant_id: TenantId) -> ValidationResult:
        """Validate that a tenant exists and is active."""
        if not self._tenant_repo:
            return ValidationResult.success()

        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return ValidationResult.failure(
                f"Tenant {tenant_id.value} does not exist"
            )
        
        # Check tenant status (assuming tenant has is_active method or status)
        if hasattr(tenant, '_status'):
            from app.domain.enums import TenantStatus
            if tenant._status != TenantStatus.ACTIVE:
                return ValidationResult.failure(
                    f"Tenant {tenant_id.value} is not active"
                )
        
        return ValidationResult.success()

    # =========================================================================
    # CLIENT VALIDATION
    # =========================================================================

    async def validate_client_exists(self, client_id: ClientId) -> ValidationResult:
        """Validate that a client exists."""
        if not self._client_repo:
            return ValidationResult.success()

        client = await self._client_repo.get_by_id(client_id)
        if not client:
            return ValidationResult.failure(
                f"Client {client_id.value} does not exist"
            )
        return ValidationResult.success()

    async def validate_client_active(self, client_id: ClientId) -> ValidationResult:
        """Validate that a client exists and is active."""
        if not self._client_repo:
            return ValidationResult.success()

        client = await self._client_repo.get_by_id(client_id)
        if not client:
            return ValidationResult.failure(
                f"Client {client_id.value} does not exist"
            )

        if hasattr(client, 'is_active') and not client.is_active():
            return ValidationResult.failure(
                f"Client {client_id.value} is not active"
            )

        return ValidationResult.success()

    # =========================================================================
    # CONTRACT VALIDATION
    # =========================================================================

    async def validate_contract_exists(self, contract_id: ContractId) -> ValidationResult:
        """Validate that a contract exists."""
        if not self._contract_repo:
            return ValidationResult.success()

        contract = await self._contract_repo.get_by_id(contract_id)
        if not contract:
            return ValidationResult.failure(
                f"Contract {contract_id.value} does not exist"
            )
        return ValidationResult.success()

    async def validate_client_has_active_contract(
        self, client_id: ClientId
    ) -> ValidationResult:
        """Validate that a client has an active contract."""
        if not self._contract_repo:
            return ValidationResult.success()

        contracts = await self._contract_repo.get_active_by_client(client_id)
        if not contracts:
            return ValidationResult.failure(
                f"Client {client_id.value} does not have an active contract"
            )
        return ValidationResult.success()

    # =========================================================================
    # PERSON VALIDATION
    # =========================================================================

    async def validate_person_exists(self, person_id: PersonId) -> ValidationResult:
        """Validate that a person exists."""
        if not self._person_repo:
            return ValidationResult.success()

        person = await self._person_repo.get_by_id(person_id)
        if not person:
            return ValidationResult.failure(
                f"Person {person_id.value} does not exist"
            )
        return ValidationResult.success()

    async def validate_person_active(self, person_id: PersonId) -> ValidationResult:
        """Validate that a person exists and is active."""
        if not self._person_repo:
            return ValidationResult.success()

        person = await self._person_repo.get_by_id(person_id)
        if not person:
            return ValidationResult.failure(
                f"Person {person_id.value} does not exist"
            )

        if hasattr(person, '_status') and person._status != BaseStatus.ACTIVE:
            return ValidationResult.failure(
                f"Person {person_id.value} is not active"
            )

        return ValidationResult.success()

    # =========================================================================
    # SERVICE VALIDATION
    # =========================================================================

    async def validate_service_exists(self, service_id: ServiceId) -> ValidationResult:
        """Validate that a service exists."""
        if not self._service_repo:
            return ValidationResult.success()

        service = await self._service_repo.get_by_id(service_id)
        if not service:
            return ValidationResult.failure(
                f"Service {service_id.value} does not exist"
            )
        return ValidationResult.success()

    async def validate_service_active(self, service_id: ServiceId) -> ValidationResult:
        """Validate that a service exists and is active."""
        if not self._service_repo:
            return ValidationResult.success()

        service = await self._service_repo.get_by_id(service_id)
        if not service:
            return ValidationResult.failure(
                f"Service {service_id.value} does not exist"
            )

        if hasattr(service, '_status') and service._status != BaseStatus.ACTIVE:
            return ValidationResult.failure(
                f"Service {service_id.value} is not active"
            )

        return ValidationResult.success()

    # =========================================================================
    # USER VALIDATION
    # =========================================================================

    async def validate_user_exists(self, user_id: UserId) -> ValidationResult:
        """Validate that a user exists."""
        if not self._user_repo:
            return ValidationResult.success()

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return ValidationResult.failure(
                f"User {user_id.value} does not exist"
            )
        return ValidationResult.success()

    async def validate_user_active(self, user_id: UserId) -> ValidationResult:
        """Validate that a user exists and is active."""
        if not self._user_repo:
            return ValidationResult.success()

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return ValidationResult.failure(
                f"User {user_id.value} does not exist"
            )

        if hasattr(user, 'is_active') and not user.is_active():
            return ValidationResult.failure(
                f"User {user_id.value} is not active"
            )

        return ValidationResult.success()

    # =========================================================================
    # COMPOSITE VALIDATION
    # =========================================================================

    async def validate_contract_creation(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
    ) -> ValidationResult:
        """
        Validate all preconditions for creating a contract.
        
        Checks:
        - Tenant exists and is active
        - Client exists and is active
        """
        result = ValidationResult.success()

        tenant_result = await self.validate_tenant_active(tenant_id)
        result = result.merge(tenant_result)

        client_result = await self.validate_client_active(client_id)
        result = result.merge(client_result)

        return result

    async def validate_service_session_creation(
        self,
        tenant_id: TenantId,
        service_id: ServiceId,
        person_id: PersonId,
        provider_id: PersonId,
    ) -> ValidationResult:
        """
        Validate all preconditions for creating a service session.
        
        Checks:
        - Tenant exists and is active
        - Service exists and is active
        - Person (client) exists and is active
        - Provider exists and is active
        """
        result = ValidationResult.success()

        tenant_result = await self.validate_tenant_active(tenant_id)
        result = result.merge(tenant_result)

        service_result = await self.validate_service_active(service_id)
        result = result.merge(service_result)

        person_result = await self.validate_person_active(person_id)
        result = result.merge(person_result)

        provider_result = await self.validate_person_active(provider_id)
        result = result.merge(provider_result)

        return result

    async def validate_service_assignment_creation(
        self,
        tenant_id: TenantId,
        service_id: ServiceId,
        contract_id: ContractId,
    ) -> ValidationResult:
        """
        Validate all preconditions for creating a service assignment.
        
        Checks:
        - Tenant exists and is active
        - Service exists and is active
        - Contract exists
        """
        result = ValidationResult.success()

        tenant_result = await self.validate_tenant_active(tenant_id)
        result = result.merge(tenant_result)

        service_result = await self.validate_service_active(service_id)
        result = result.merge(service_result)

        contract_result = await self.validate_contract_exists(contract_id)
        result = result.merge(contract_result)

        return result
