"""Repository dependency factories for the clinical bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.case_referral_source_repository import (
    CaseReferralSourceRepository,
)
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.clinical_note_repository import (
    ClinicalNoteRepository,
)
from app.domain.repositories.eap_programme_repository import (
    AuthorizationRepository,
    EAPProgrammeRepository,
)
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
)
from app.domain.repositories.member_import_repository import MemberImportRepository
from app.domain.repositories.member_next_of_kin_repository import MemberNextOfKinRepository
from app.domain.repositories.next_of_kin_relationship_repository import (
    NextOfKinRelationshipRepository,
)
from app.domain.repositories.presenting_problem_repository import (
    PresentingProblemRepository,
)


async def get_case_repository(
    db: AsyncSession = Depends(get_db),
) -> "CaseRepository":
    from app.infrastructure.repositories.case_repository import (
        CaseRepositoryImpl,
    )

    return CaseRepositoryImpl(db)


async def get_presenting_problem_repository(
    db: AsyncSession = Depends(get_db),
) -> "PresentingProblemRepository":
    from app.infrastructure.repositories.presenting_problem_repository import (
        PresentingProblemRepositoryImpl,
    )

    return PresentingProblemRepositoryImpl(db)


async def get_case_referral_source_repository(
    db: AsyncSession = Depends(get_db),
) -> "CaseReferralSourceRepository":
    from app.infrastructure.repositories.case_referral_source_repository import (
        CaseReferralSourceRepositoryImpl,
    )

    return CaseReferralSourceRepositoryImpl(db)


async def get_clinical_note_repository(
    db: AsyncSession = Depends(get_db),
) -> "ClinicalNoteRepository":
    from app.infrastructure.repositories.clinical_note_repository import (
        ClinicalNoteRepositoryImpl,
    )

    return ClinicalNoteRepositoryImpl(db)


async def get_eap_programme_repository(
    db: AsyncSession = Depends(get_db),
) -> "EAPProgrammeRepository":
    from app.infrastructure.repositories.eap_programme_repository import (
        EAPProgrammeRepositoryImpl,
    )

    return EAPProgrammeRepositoryImpl(db)


async def get_authorization_repository(
    db: AsyncSession = Depends(get_db),
) -> "AuthorizationRepository":
    from app.infrastructure.repositories.eap_programme_repository import (
        AuthorizationRepositoryImpl,
    )

    return AuthorizationRepositoryImpl(db)


async def get_eligible_member_repository(
    db: AsyncSession = Depends(get_db),
) -> "EligibleMemberRepository":
    from app.infrastructure.repositories.eligible_member_repository import (
        EligibleMemberRepositoryImpl,
    )

    return EligibleMemberRepositoryImpl(db)


async def get_clinical_subject_repository(
    db: AsyncSession = Depends(get_db),
) -> "ClinicalSubjectRepository":
    from app.infrastructure.repositories.eligible_member_repository import (
        ClinicalSubjectRepositoryImpl,
    )

    return ClinicalSubjectRepositoryImpl(db)


async def get_member_import_repository(
    db: AsyncSession = Depends(get_db),
) -> "MemberImportRepository":
    from app.infrastructure.repositories.member_import_repository import (
        MemberImportRepositoryImpl,
    )

    return MemberImportRepositoryImpl(db)


async def get_eligible_member_clinical_link_repository(
    db: AsyncSession = Depends(get_db),
) -> "EligibleMemberClinicalLinkRepository":
    from app.infrastructure.repositories.eligible_member_repository import (
        EligibleMemberClinicalLinkRepositoryImpl,
    )

    return EligibleMemberClinicalLinkRepositoryImpl(db)


async def get_member_next_of_kin_repository(
    db: AsyncSession = Depends(get_db),
) -> "MemberNextOfKinRepository":
    from app.infrastructure.repositories.member_next_of_kin_repository import (
        MemberNextOfKinRepositoryImpl,
    )

    return MemberNextOfKinRepositoryImpl(db)


async def get_next_of_kin_relationship_repository(
    db: AsyncSession = Depends(get_db),
) -> "NextOfKinRelationshipRepository":
    from app.infrastructure.repositories.next_of_kin_relationship_repository import (
        NextOfKinRelationshipRepositoryImpl,
    )

    return NextOfKinRelationshipRepositoryImpl(db)
