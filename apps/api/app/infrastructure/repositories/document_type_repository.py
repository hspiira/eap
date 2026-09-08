"""SQLAlchemy implementation of the document type repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document_type import DocumentType
from app.domain.repositories.document_type_repository import DocumentTypeRepository
from app.infrastructure.models.document_type_model import DocumentTypeModel
from app.shared.utils.generators import generate_cuid


def _apply(model, **fields) -> bool:
    changed = False
    for key, value in fields.items():
        if value is not None and getattr(model, key) != value:
            setattr(model, key, value)
            changed = True
    return changed


def _to_entity(model: DocumentTypeModel) -> DocumentType:
    return DocumentType(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


class DocumentTypeRepositoryImpl(DocumentTypeRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, *, active_only: bool = True) -> list[DocumentType]:
        stmt = select(DocumentTypeModel).order_by(
            DocumentTypeModel.sort_order, DocumentTypeModel.name
        )
        if active_only:
            stmt = stmt.where(
                DocumentTypeModel.is_active.is_(True),
                DocumentTypeModel.effective_until.is_(None),
            )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars()]

    async def get_by_code(self, code: str) -> DocumentType | None:
        stmt = select(DocumentTypeModel).where(DocumentTypeModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_id(self, type_id: str) -> DocumentType | None:
        model = await self._session.get(DocumentTypeModel, type_id)
        return _to_entity(model) if model else None

    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> DocumentType:
        model = DocumentTypeModel(
            id=generate_cuid(),
            code=code,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def update(
        self,
        type_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> DocumentType | None:
        model = await self._session.get(DocumentTypeModel, type_id)
        if model is None:
            return None
        if _apply(model, name=name, description=description, sort_order=sort_order):
            model.version += 1
        await self._session.flush()
        return _to_entity(model)

    async def set_active(self, type_id: str, *, is_active: bool) -> DocumentType | None:
        model = await self._session.get(DocumentTypeModel, type_id)
        if model is None:
            return None
        model.is_active = is_active
        model.effective_until = None if is_active else datetime.now(UTC)
        await self._session.flush()
        return _to_entity(model)
