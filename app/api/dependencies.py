"""
API Dependencies

FastAPI dependency injection helpers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.benchmark_consent_repository import (
    BenchmarkConsentRepository,
)
from app.domain.repositories.care_callback_repository import (
    CareCallbackCampaignRepository,
    OutreachRecordRepository,
)
from app.domain.repositories.critical_incident_repository import (
    CriticalIncidentRepository,
)
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.domain.repositories.dsar_repository import DSARRequestRepository
from app.domain.repositories.engagement_repository import EngagementRepository
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.repositories.report_repository import (
    ReportRunRepository,
    ReportTemplateRepository,
)
from app.domain.repositories.survey_repository import (
    SurveyCampaignRepository,
    SurveyResponseRepository,
)
from app.domain.repositories.utilisation_event_repository import (
    UtilisationEventRepository,
)
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.activity_repository import ActivityRepository
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.service_assignment_repository import (
    ServiceAssignmentRepository,
)
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.repositories.service_session_repository import (
    ServiceSessionRepository,
)
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.client_repository import ClientRepositoryImpl
from app.infrastructure.repositories.contract_repository import ContractRepositoryImpl
from app.infrastructure.repositories.activity_repository import ActivityRepositoryImpl
from app.infrastructure.repositories.password_set_token_repository import (
    PasswordSetTokenRepository,
)
from app.infrastructure.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.infrastructure.repositories.client_tag_repository import ClientTagRepositoryImpl
from app.infrastructure.repositories.contact_repository import ContactRepositoryImpl
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl
from app.infrastructure.repositories.industry_repository import IndustryRepositoryImpl
from app.infrastructure.repositories.kpi_repository import (
    KPIAssignmentRepositoryImpl,
    KPIRepositoryImpl,
)
from app.infrastructure.repositories.person_repository import PersonRepositoryImpl
from app.infrastructure.repositories.service_assignment_repository import (
    ServiceAssignmentRepositoryImpl,
)
from app.infrastructure.repositories.service_repository import ServiceRepositoryImpl
from app.infrastructure.repositories.service_session_repository import (
    ServiceSessionRepositoryImpl,
)
from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.shared.handlers.audit_event_handler import AuditEventHandler


async def get_tenant_repository(
    db: AsyncSession = Depends(get_db),
) -> TenantRepository:
    """
    Dependency for getting tenant repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        TenantRepository implementation
    """
    return TenantRepositoryImpl(db)


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """
    Dependency for getting user repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        UserRepository implementation
    """
    return UserRepositoryImpl(db)


async def get_password_set_token_repository(
    db: AsyncSession = Depends(get_db),
) -> PasswordSetTokenRepository:
    """Dependency for password set token store (tenant creation set-password flow)."""
    return PasswordSetTokenRepository(db)


async def get_client_repository(
    db: AsyncSession = Depends(get_db),
) -> ClientRepository:
    """
    Dependency for getting client repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ClientRepository implementation
    """
    return ClientRepositoryImpl(db)


async def get_person_repository(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
) -> PersonRepository:
    """
    Dependency for getting person repository.

    Args:
        db: Database session (injected by FastAPI)
        user_repo: User repository (injected dependency)

    Returns:
        PersonRepository implementation
    """
    return PersonRepositoryImpl(db, user_repo)


async def get_contract_repository(
    db: AsyncSession = Depends(get_db),
) -> ContractRepository:
    """
    Dependency for getting contract repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ContractRepository implementation
    """
    return ContractRepositoryImpl(db)


async def get_audit_repository(
    db: AsyncSession = Depends(get_db),
) -> AuditRepository:
    """
    Dependency for getting audit repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AuditRepository implementation
    """
    return AuditRepositoryImpl(db)


async def get_service_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceRepository:
    """
    Dependency for getting service repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceRepository implementation
    """
    return ServiceRepositoryImpl(db)


async def get_service_session_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceSessionRepository:
    """
    Dependency for getting service session repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceSessionRepository implementation
    """
    return ServiceSessionRepositoryImpl(db)


async def get_document_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    """
    Dependency for getting document repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        DocumentRepository implementation
    """
    return DocumentRepositoryImpl(db)


async def get_kpi_repository(
    db: AsyncSession = Depends(get_db),
) -> KPIRepository:
    """
    Dependency for getting KPI repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        KPIRepository implementation
    """
    return KPIRepositoryImpl(db)


async def get_kpi_assignment_repository(
    db: AsyncSession = Depends(get_db),
) -> KPIAssignmentRepository:
    """
    Dependency for getting KPI assignment repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        KPIAssignmentRepository implementation
    """
    return KPIAssignmentRepositoryImpl(db)


async def get_industry_repository(
    db: AsyncSession = Depends(get_db),
) -> IndustryRepository:
    """
    Dependency for getting industry repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        IndustryRepository implementation
    """
    return IndustryRepositoryImpl(db)


async def get_client_tag_repository(
    db: AsyncSession = Depends(get_db),
) -> ClientTagRepository:
    """
    Dependency for getting client tag repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ClientTagRepository implementation
    """
    return ClientTagRepositoryImpl(db)


async def get_contact_repository(
    db: AsyncSession = Depends(get_db),
) -> ContactRepository:
    """
    Dependency for getting contact repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ContactRepository implementation
    """
    return ContactRepositoryImpl(db)


async def get_activity_repository(
    db: AsyncSession = Depends(get_db),
) -> ActivityRepository:
    """
    Dependency for getting activity repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ActivityRepository implementation
    """
    return ActivityRepositoryImpl(db)


async def get_service_assignment_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceAssignmentRepository:
    """
    Dependency for getting service assignment repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceAssignmentRepository implementation
    """
    return ServiceAssignmentRepositoryImpl(db)


async def get_outbox_repository(
    db: AsyncSession = Depends(get_db),
) -> "OutboxRepository":
    from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl

    return OutboxRepositoryImpl(db)


async def get_audit_event_handler(
    outbox_repo: "OutboxRepository" = Depends(get_outbox_repository),
) -> AuditEventHandler:
    """Audit handler enqueues domain events on the transactional outbox."""
    return AuditEventHandler(outbox_repo)


async def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    """Dependency for refresh token repository (revocation/rotation)."""
    return RefreshTokenRepository(db)


async def get_diagnosis_repository(
    db: AsyncSession = Depends(get_db),
) -> "DiagnosisRepository":
    from app.infrastructure.repositories.diagnosis_repository import (
        DiagnosisRepositoryImpl,
    )

    return DiagnosisRepositoryImpl(db)


async def get_critical_incident_repository(
    db: AsyncSession = Depends(get_db),
) -> "CriticalIncidentRepository":
    from app.infrastructure.repositories.critical_incident_repository import (
        CriticalIncidentRepositoryImpl,
    )

    return CriticalIncidentRepositoryImpl(db)


async def get_non_compete_clause_repository(
    db: AsyncSession = Depends(get_db),
) -> "NonCompeteClauseRepository":
    from app.infrastructure.repositories.non_compete_clause_repository import (
        NonCompeteClauseRepositoryImpl,
    )

    return NonCompeteClauseRepositoryImpl(db)


async def get_report_template_repository(
    db: AsyncSession = Depends(get_db),
) -> "ReportTemplateRepository":
    from app.infrastructure.repositories.report_repository import (
        ReportTemplateRepositoryImpl,
    )

    return ReportTemplateRepositoryImpl(db)


async def get_report_run_repository(
    db: AsyncSession = Depends(get_db),
) -> "ReportRunRepository":
    from app.infrastructure.repositories.report_repository import (
        ReportRunRepositoryImpl,
    )

    return ReportRunRepositoryImpl(db)


async def get_report_query_runner(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.report_query_runner import ReportQueryRunner

    return ReportQueryRunner(db)


async def get_utilisation_event_repository(
    db: AsyncSession = Depends(get_db),
) -> "UtilisationEventRepository":
    from app.infrastructure.repositories.utilisation_event_repository import (
        UtilisationEventRepositoryImpl,
    )

    return UtilisationEventRepositoryImpl(db)


async def get_care_callback_campaign_repository(
    db: AsyncSession = Depends(get_db),
) -> "CareCallbackCampaignRepository":
    from app.infrastructure.repositories.care_callback_repository import (
        CareCallbackCampaignRepositoryImpl,
    )

    return CareCallbackCampaignRepositoryImpl(db)


async def get_outreach_record_repository(
    db: AsyncSession = Depends(get_db),
) -> "OutreachRecordRepository":
    from app.infrastructure.repositories.care_callback_repository import (
        OutreachRecordRepositoryImpl,
    )

    return OutreachRecordRepositoryImpl(db)


async def get_engagement_repository(
    db: AsyncSession = Depends(get_db),
) -> "EngagementRepository":
    from app.infrastructure.repositories.engagement_repository import (
        EngagementRepositoryImpl,
    )

    return EngagementRepositoryImpl(db)


async def get_dsar_request_repository(
    db: AsyncSession = Depends(get_db),
) -> "DSARRequestRepository":
    from app.infrastructure.repositories.dsar_repository import (
        DSARRequestRepositoryImpl,
    )

    return DSARRequestRepositoryImpl(db)


async def get_dsar_collector(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.dsar_service import SqlDSARDataCollector

    return SqlDSARDataCollector(db)


async def get_benchmark_consent_repository(
    db: AsyncSession = Depends(get_db),
) -> "BenchmarkConsentRepository":
    from app.infrastructure.repositories.benchmark_consent_repository import (
        BenchmarkConsentRepositoryImpl,
    )

    return BenchmarkConsentRepositoryImpl(db)


async def get_benchmark_collector(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.benchmark_collector import (
        SqlBenchmarkCollector,
    )

    return SqlBenchmarkCollector(db)


async def get_dsar_tombstoner(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.dsar_service import SqlDSARTombstoner

    return SqlDSARTombstoner(db)


async def get_survey_campaign_repository(
    db: AsyncSession = Depends(get_db),
) -> "SurveyCampaignRepository":
    from app.infrastructure.repositories.survey_repository import (
        SurveyCampaignRepositoryImpl,
    )

    return SurveyCampaignRepositoryImpl(db)


async def get_survey_response_repository(
    db: AsyncSession = Depends(get_db),
) -> "SurveyResponseRepository":
    from app.infrastructure.repositories.survey_repository import (
        SurveyResponseRepositoryImpl,
    )

    return SurveyResponseRepositoryImpl(db)


# =============================================================================
# VALIDATION SERVICE
# =============================================================================


from app.application.services.validation_service import ValidationService  # noqa: E402


async def get_validation_service(
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    person_repo: PersonRepository = Depends(get_person_repository),
    service_repo: ServiceRepository = Depends(get_service_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> ValidationService:
    """
    Dependency for getting validation service.

    The validation service provides cross-entity validation
    that spans multiple aggregates.

    Args:
        tenant_repo: Tenant repository
        client_repo: Client repository
        contract_repo: Contract repository
        person_repo: Person repository
        service_repo: Service repository
        user_repo: User repository

    Returns:
        ValidationService instance
    """
    return ValidationService(
        tenant_repo=tenant_repo,
        client_repo=client_repo,
        contract_repo=contract_repo,
        person_repo=person_repo,
        service_repo=service_repo,
        user_repo=user_repo,
    )


# =============================================================================
# EVENT BUS
# =============================================================================


from app.shared.events.event_bus import EventBus, event_bus  # noqa: E402


def get_event_bus() -> EventBus:
    """
    Dependency for getting the event bus.

    Returns the global event bus instance.

    Returns:
        EventBus instance
    """
    return event_bus
