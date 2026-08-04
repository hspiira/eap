"""EAP programme + Authorization use cases."""

from __future__ import annotations

from datetime import date

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.authorization import Authorization
from app.domain.entities.eap_programme import EAPProgramme
from app.domain.enums import (
    AuthorizationStatus,
    RelationType,
    ServiceCategory,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.eap_programme_repository import (
    AuthorizationRepository,
    EAPProgrammeRepository,
)
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ContractId,
    EAPProgrammeId,
    TenantId,
    UserId,
)
from app.domain.value_objects.programme import ProgrammeSessionCap
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class CreateEAPProgrammeUseCase(BaseUseCase[EAPProgramme, EAPProgrammeId]):
    def __init__(self, repository: EAPProgrammeRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        programme_id: EAPProgrammeId,
        tenant_id: TenantId,
        contract_id: ContractId,
        name: str,
        effective_from: date,
        caps: tuple[ProgrammeSessionCap, ...],
        eligible_dependent_relations: tuple[RelationType, ...] = (),
        effective_until: date | None = None,
        geographic_scope: str | None = None,
        description: str | None = None,
        created_by: UserId | None = None,
    ) -> EAPProgramme:
        now = utc_now()
        programme = EAPProgramme(
            id=programme_id,
            tenant_id=tenant_id,
            contract_id=contract_id,
            name=name,
            effective_from=effective_from,
            effective_until=effective_until,
            caps=caps,
            eligible_dependent_relations=eligible_dependent_relations,
            geographic_scope=geographic_scope,
            description=description,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(programme)


class AuthorizeCaseUseCase:
    """Instantiate a per-Case Authorization from a programme cap."""

    def __init__(
        self,
        programme_repository: EAPProgrammeRepository,
        authorization_repository: AuthorizationRepository,
        case_repository: CaseRepository,
    ):
        self._programmes = programme_repository
        self._authorizations = authorization_repository
        self._cases = case_repository

    async def execute(
        self,
        *,
        case_id: CaseId,
        programme_id: EAPProgrammeId,
        service_category: ServiceCategory,
        expires_on: date | None = None,
    ) -> Authorization:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise NotFoundError(
                f"Case not found: {case_id.value}",
                resource_type="Case",
                resource_id=case_id.value,
            )
        programme = await self._programmes.get_by_id(programme_id)
        if programme is None:
            raise NotFoundError(
                f"Programme not found: {programme_id.value}",
                resource_type="EAPProgramme",
                resource_id=programme_id.value,
            )
        if programme.tenant_id != case.tenant_id:
            raise DomainError("Programme tenant does not match case tenant")
        if not programme.is_currently_effective():
            raise DomainError("Programme is not currently effective")
        cap = programme.cap_for(service_category)
        if cap is None:
            raise DomainError(f"Programme has no cap for {service_category.value}")
        now = utc_now()
        authorization = Authorization(
            id=AuthorizationId(generate_cuid()),
            tenant_id=case.tenant_id,
            case_id=case.id,
            clinical_subject_id=case.clinical_subject_id,
            programme_id=programme.id,
            service_category=service_category,
            sessions_granted=cap.per_issue_per_year,
            sessions_used=0,
            status=AuthorizationStatus.ACTIVE,
            granted_at=now,
            expires_on=expires_on,
            created_at=now,
            updated_at=now,
        )
        await self._authorizations.save(authorization)
        case.attach_authorization(authorization.id)
        await self._cases.save(case)
        return authorization


class ConsumeAuthorizationSessionUseCase:
    def __init__(self, repository: AuthorizationRepository):
        self._repo = repository

    async def execute(self, authorization_id: AuthorizationId) -> Authorization:
        auth = await self._repo.get_by_id(authorization_id)
        if auth is None:
            raise NotFoundError(
                f"Authorization not found: {authorization_id.value}",
                resource_type="Authorization",
                resource_id=authorization_id.value,
            )
        auth.consume_session()
        await self._repo.save(auth)
        return auth


class RequestAuthorizationExtensionUseCase:
    def __init__(self, repository: AuthorizationRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        authorization_id: AuthorizationId,
        additional_sessions: int,
        requested_by: UserId,
    ) -> Authorization:
        auth = await self._repo.get_by_id(authorization_id)
        if auth is None:
            raise NotFoundError(
                f"Authorization not found: {authorization_id.value}",
                resource_type="Authorization",
                resource_id=authorization_id.value,
            )
        auth.request_extension(
            additional_sessions=additional_sessions,
            requested_by=requested_by,
        )
        await self._repo.save(auth)
        return auth


class GrantAuthorizationExtensionUseCase:
    def __init__(self, repository: AuthorizationRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        authorization_id: AuthorizationId,
        clinician_signoff: UserId,
        admin_signoff: UserId,
    ) -> Authorization:
        if clinician_signoff == admin_signoff:
            raise DomainError("Clinician and admin sign-offs must come from different users")
        auth = await self._repo.get_by_id(authorization_id)
        if auth is None:
            raise NotFoundError(
                f"Authorization not found: {authorization_id.value}",
                resource_type="Authorization",
                resource_id=authorization_id.value,
            )
        auth.grant_extension(
            clinician_signoff=clinician_signoff,
            admin_signoff=admin_signoff,
        )
        await self._repo.save(auth)
        return auth
