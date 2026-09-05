"""Repository dependency factories for the clinical bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
from app.domain.repositories.member_next_of_kin_repository import MemberNextOfKinRepository


async def get_case_repository(
    db: AsyncSession = Depends(get_db),
) -> "CaseRepository":
    from app.infrastructure.repositories.case_repository import (
        CaseRepositoryImpl,
    )

    return CaseRepositoryImpl(db)


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
