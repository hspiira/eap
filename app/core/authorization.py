"""
Authorization Module

Centralized tenant and resource ownership checks.

Tenant from token: The canonical "current tenant" is always current_user.tenant_id
(from the JWT). Any client-supplied tenant_id (path, query, or body) must be
validated against it via require_same_tenant(tenant_id); never use client
tenant_id alone for scoping. Prefer path design that does not require the client
to send tenant_id (e.g. /me/... or /tenant/...) where feasible.

Use require_same_tenant when the route already has tenant_id in path/query.
Use get_*_for_current_tenant (or get_user_in_tenant) for by-ID routes so tenant
is derived from the loaded entity.
"""

from fastapi import Depends, HTTPException, status

from app.api.dependencies import (
    get_audit_repository,
    get_client_repository,
    get_contract_repository,
    get_document_repository,
    get_industry_repository,
    get_person_repository,
    get_service_repository,
    get_service_session_repository,
    get_user_repository,
)
from app.core.config import settings
from app.core.security import TokenData, get_current_user, get_current_user_optional
from app.domain.entities.audit import AuditLog
from app.domain.entities.client import ClientEntity
from app.domain.entities.contract import ContractEntity
from app.domain.entities.document import DocumentEntity
from app.domain.entities.industry import IndustryEntity
from app.domain.entities.person import PersonEntity
from app.domain.entities.service import ServiceEntity
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import AccessScope, TenantRole
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.repositories.service_session_repository import ServiceSessionRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    AuditLogId,
    ClientId,
    ContractId,
    DocumentId,
    IndustryId,
    PersonId,
    ServiceId,
    SessionId,
    UserId,
)


async def get_current_user_entity(
    current_user: TokenData = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserEntity:
    """
    Load the full current user entity (for RBAC role checks).
    Use when you need current_user.tenant_id and the user's tenant role.
    """
    user = await user_repo.get_by_id(UserId(current_user.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )
    return user


def require_tenant_role(*allowed_roles: TenantRole):
    """
    Dependency factory: require that the current user's tenant role is in allowed_roles.
    Use for tenant management (activate, suspend, terminate, settings) and user management (ban, terminate, etc.).
    """

    async def _require(
        current_user_entity: UserEntity = Depends(get_current_user_entity),
    ) -> UserEntity:
        if current_user_entity.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this action",
            )
        return current_user_entity

    return _require


async def require_not_viewer(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Use as ``Depends(require_not_viewer)`` on every write/mutation route to
    block Viewer-role users without an extra DB round-trip.  The role is read
    directly from the JWT claim embedded at token-mint time.

    Viewers may read but must not create, update, or delete.
    Returns the caller's TokenData so the handler can use it if needed.
    """
    if current_user.role == TenantRole.VIEWER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role: Viewers cannot perform write operations",
        )
    return current_user


def require_self_or_role(*allowed_roles: TenantRole):
    """
    Dependency factory: allow self-actions (caller acts on their own user_id)
    OR users whose tenant role is in allowed_roles.

    Use for endpoints that should be self-service for the target user but
    overridable by admins — e.g. password change, 2FA toggle, preferences.

    Requires the route to declare `user_id: str` as a path/query param so
    FastAPI resolves it before this dependency runs.
    """

    async def _require(
        user_id: str,
        current_user_entity: UserEntity = Depends(get_current_user_entity),
    ) -> UserEntity:
        if current_user_entity.id.value == user_id:
            return current_user_entity
        if current_user_entity.role in allowed_roles:
            return current_user_entity
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only perform this action on yourself, or as an admin",
        )

    return _require


async def require_same_tenant(
    tenant_id: str,
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Require that the current user belongs to the given tenant.
    Use for routes that have tenant_id in path or query.
    """
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )
    return current_user


def _token_has_scope(token: TokenData, scope: AccessScope) -> bool:
    return scope.value in (token.access_scopes or [])


def require_scope(*allowed_scopes: AccessScope, fail_closed_on_legacy: bool | None = None):
    """Dependency factory enforcing the bounded-context access-scope split.

    A token is admitted when *any* of ``allowed_scopes`` appears in its
    ``access_scopes`` claim.

    Tokens minted before the scope rollout carry no claim, and are admitted so
    the rollout could be incremental — which means they bypass the scope wall
    entirely. That is governed by ``SCOPE_FAIL_CLOSED_ON_LEGACY``, so the cutover
    is a per-environment config change rather than a deploy. Pass
    ``fail_closed_on_legacy=True`` to refuse them on a given route regardless.

    See §4 of 11_RELEASE_RUNBOOK_AND_OPEN_ACTIONS.md — this needs a date.
    """

    allowed = {s.value for s in allowed_scopes}

    async def _require(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        fail_closed = (
            settings.SCOPE_FAIL_CLOSED_ON_LEGACY
            if fail_closed_on_legacy is None
            else fail_closed_on_legacy
        )
        scopes = current_user.access_scopes or []
        if not scopes and not fail_closed:
            return current_user
        if any(s in allowed for s in scopes):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Access scope insufficient for this route; "
                f"required one of {sorted(allowed)}"
            ),
        )

    return _require


require_clinical_scope = require_scope(
    AccessScope.CLINICAL, AccessScope.PLATFORM_ADMIN
)
"""Use as ``Depends(require_clinical_scope)`` on every clinical-only route."""


require_employer_scope = require_scope(
    AccessScope.EMPLOYER_PORTAL, AccessScope.PLATFORM_ADMIN
)
"""Use as ``Depends(require_employer_scope)`` on employer-portal routes."""


async def require_platform_admin(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Require that the current user is a platform admin.
    When PLATFORM_TENANT_ID is set, users in that tenant are platform admins.
    """
    platform_tenant_id = getattr(
        settings, "PLATFORM_TENANT_ID", ""
    ).strip()
    if not platform_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin required",
        )
    if current_user.tenant_id != platform_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin required",
        )
    return current_user


async def require_platform_admin_if_configured(
    current_user: TokenData | None = Depends(get_current_user_optional),
) -> None:
    """
    When REQUIRE_PLATFORM_ADMIN_FOR_TENANT_CREATION is True, require auth and platform admin (401/403).
    When False, no-op. Use on POST /tenants to optionally restrict tenant creation.
    """
    if not settings.REQUIRE_PLATFORM_ADMIN_FOR_TENANT_CREATION:
        return
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for tenant creation",
            headers={"WWW-Authenticate": "Bearer"},
        )
    platform_tenant_id = getattr(settings, "PLATFORM_TENANT_ID", "").strip()
    if not platform_tenant_id or current_user.tenant_id != platform_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin required for tenant creation",
        )


async def get_user_in_tenant(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserEntity:
    """
    Load user by ID and require that the user belongs to the current user's tenant.
    Use for routes that take user_id in path (activate, suspend, terminate, etc.).
    """
    user = await user_repo.get_by_id(UserId(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )
    return user


async def get_industry_in_tenant(
    industry_id: str,
    current_user: TokenData = Depends(get_current_user),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
) -> IndustryEntity:
    """
    Load industry by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found, 403 if cross-tenant.
    """
    industry = await industry_repo.get_by_id(IndustryId(industry_id))
    if not industry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Industry not found",
        )
    if industry.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )
    return industry


async def get_audit_log_for_current_tenant(
    audit_log_id: str,
    current_user: TokenData = Depends(get_current_user),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> AuditLog:
    """
    Load audit log by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    audit_log = await audit_repo.get_audit_log_by_id(AuditLogId(audit_log_id))
    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )
    if audit_log.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )
    return audit_log


async def get_document_for_current_tenant(
    document_id: str,
    current_user: TokenData = Depends(get_current_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentEntity:
    """
    Load document by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    document = await document_repo.get_by_id(DocumentId(document_id))
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


async def get_client_for_current_tenant(
    client_id: str,
    current_user: TokenData = Depends(get_current_user),
    client_repo: ClientRepository = Depends(get_client_repository),
) -> ClientEntity:
    """
    Load client by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    client = await client_repo.get_by_id(ClientId(client_id))
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    if client.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return client


async def get_contract_for_current_tenant(
    contract_id: str,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
) -> ContractEntity:
    """
    Load contract by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    contract = await contract_repo.get_by_id(ContractId(contract_id))
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    if contract.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    return contract


async def get_service_for_current_tenant(
    service_id: str,
    current_user: TokenData = Depends(get_current_user),
    service_repo: ServiceRepository = Depends(get_service_repository),
) -> ServiceEntity:
    """
    Load service by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    service = await service_repo.get_by_id(ServiceId(service_id))
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    if service.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return service


async def get_service_session_for_current_tenant(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
) -> ServiceSessionEntity:
    """
    Load service session by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    session = await session_repo.get_by_id(SessionId(session_id))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service session not found",
        )
    if session.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service session not found",
        )
    return session


async def get_person_for_current_tenant(
    person_id: str,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
) -> PersonEntity:
    """
    Load person by ID and require that it belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    try:
        person = await person_repo.get_by_id(PersonId(person_id))
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        ) from err
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    if person.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    return person


async def get_person_by_user_id_for_current_tenant(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
) -> PersonEntity:
    """
    Load person by user ID and require that the person belongs to the current user's tenant.
    Returns 404 if not found or different tenant (fail closed).
    """
    person = await person_repo.get_by_user_id(UserId(user_id))
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    if person.tenant_id.value != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    return person
