"""Clinical note routes — CLINICAL-scope only."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_case_repository,
    get_clinical_note_repository,
)
from app.api.schemas.clinical_note_schemas import (
    AmendClinicalNoteRequest,
    ClinicalNoteResponse,
    CreateClinicalNoteRequest,
    NoteAmendmentResponse,
    UpdateClinicalNoteBodyRequest,
)
from app.application.use_cases.clinical_note_use_cases import (
    AmendClinicalNoteUseCase,
    CreateClinicalNoteUseCase,
    SignClinicalNoteUseCase,
    UpdateDraftNoteBodyUseCase,
)
from app.core.authorization import require_clinical_scope, require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.clinical_note import ClinicalNote
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.clinical_note_repository import (
    ClinicalNoteRepository,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    SessionId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(tags=["clinical-notes"])


def _to_response(n: ClinicalNote) -> ClinicalNoteResponse:
    return ClinicalNoteResponse(
        id=n.id.value,
        tenant_id=n.tenant_id.value,
        case_id=n.case_id.value,
        clinical_subject_id=n.clinical_subject_id.value,
        note_type=n.note_type,
        body=n.body,
        author_id=n.author_id.value,
        session_id=n.session_id.value if n.session_id else None,
        signed_at=n.signed_at,
        signed_by=n.signed_by.value if n.signed_by else None,
        locked_at=n.locked_at,
        amendments=[
            NoteAmendmentResponse(
                id=a.id.value,
                author_id=a.author_id.value,
                body=a.body,
                reason=a.reason,
                created_at=a.created_at,
            )
            for a in n.amendments
        ],
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


@router.post(
    "/clinical-notes",
    response_model=ClinicalNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Author a draft clinical note attached to a case",
)
@transactional()
async def create_note(
    data: CreateClinicalNoteRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    note_repo: ClinicalNoteRepository = Depends(get_clinical_note_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    note = await CreateClinicalNoteUseCase(case_repo, note_repo).execute(
        case_id=CaseId(data.case_id),
        author_id=UserId(current_user.user_id),
        note_type=data.note_type,
        body=data.body,
        session_id=SessionId(data.session_id) if data.session_id else None,
    )
    await audit_entity_operation(
        entity=note,
        audit_handler=audit_handler,
        tenant_id=note.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_response(note)


@router.patch(
    "/clinical-notes/{note_id}",
    response_model=ClinicalNoteResponse,
    summary="Edit a draft note (signed notes require an amendment instead)",
)
@transactional()
async def update_note(
    note_id: str,
    data: UpdateClinicalNoteBodyRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    note_repo: ClinicalNoteRepository = Depends(get_clinical_note_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    note = await UpdateDraftNoteBodyUseCase(note_repo).execute(
        note_id=ClinicalNoteId(note_id),
        editor_id=UserId(current_user.user_id),
        body=data.body,
    )
    return _to_response(note)


@router.post(
    "/clinical-notes/{note_id}/sign",
    response_model=ClinicalNoteResponse,
    summary="Sign a draft note (only the author may sign)",
)
@transactional()
async def sign_note(
    note_id: str,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    note_repo: ClinicalNoteRepository = Depends(get_clinical_note_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    note = await SignClinicalNoteUseCase(note_repo).execute(
        note_id=ClinicalNoteId(note_id),
        signer_id=UserId(current_user.user_id),
    )
    await audit_entity_operation(
        entity=note,
        audit_handler=audit_handler,
        tenant_id=note.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_response(note)


@router.post(
    "/clinical-notes/{note_id}/amend",
    response_model=ClinicalNoteResponse,
    summary="Append an amendment to a signed note",
)
@transactional()
async def amend_note(
    note_id: str,
    data: AmendClinicalNoteRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    note_repo: ClinicalNoteRepository = Depends(get_clinical_note_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    note = await AmendClinicalNoteUseCase(note_repo).execute(
        note_id=ClinicalNoteId(note_id),
        author_id=UserId(current_user.user_id),
        body=data.body,
        reason=data.reason,
    )
    await audit_entity_operation(
        entity=note,
        audit_handler=audit_handler,
        tenant_id=note.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_response(note)


@router.get(
    "/cases/{case_id}/clinical-notes",
    response_model=list[ClinicalNoteResponse],
    summary="List clinical notes for a case",
)
@readonly()
async def list_notes_for_case(
    case_id: str,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    note_repo: ClinicalNoteRepository = Depends(get_clinical_note_repository),
    db: AsyncSession = Depends(get_db),
):
    case = await case_repo.get_by_id(CaseId(case_id))
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_same_tenant(current_user, case.tenant_id.value)
    notes = await note_repo.list_for_case(case.tenant_id, case.id)
    return [_to_response(n) for n in notes]
