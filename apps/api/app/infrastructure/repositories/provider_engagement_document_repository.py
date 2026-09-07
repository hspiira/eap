"""SQL implementation of the practitioner engagement-document checklist."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.provider_engagement_document import ProviderEngagementDocument
from app.domain.enums import EngagementDocumentKind
from app.domain.repositories.provider_engagement_document_repository import (
    ProviderEngagementDocumentRepository,
)
from app.domain.value_objects.ids import ProviderId, TenantId
from app.infrastructure.mappers.provider_engagement_document_mapper import (
    ProviderEngagementDocumentMapper,
)
from app.infrastructure.models.provider_engagement_document_model import (
    ProviderEngagementDocumentModel,
)


class ProviderEngagementDocumentRepositoryImpl(ProviderEngagementDocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_for_kind(
        self, tenant_id: TenantId, provider_id: ProviderId, kind: EngagementDocumentKind
    ) -> ProviderEngagementDocument | None:
        result = await self._session.execute(
            select(ProviderEngagementDocumentModel).where(
                ProviderEngagementDocumentModel.tenant_id == tenant_id.value,
                ProviderEngagementDocumentModel.provider_id == provider_id.value,
                ProviderEngagementDocumentModel.document_kind == kind,
            )
        )
        model = result.scalar_one_or_none()
        return ProviderEngagementDocumentMapper.to_entity(model) if model else None

    async def list_for_provider(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> list[ProviderEngagementDocument]:
        result = await self._session.execute(
            select(ProviderEngagementDocumentModel)
            .where(
                ProviderEngagementDocumentModel.tenant_id == tenant_id.value,
                ProviderEngagementDocumentModel.provider_id == provider_id.value,
            )
            .order_by(ProviderEngagementDocumentModel.document_kind.asc())
        )
        return [ProviderEngagementDocumentMapper.to_entity(model) for model in result.scalars()]

    async def save(self, entity: ProviderEngagementDocument) -> None:
        model = ProviderEngagementDocumentMapper.to_model(entity)
        existing = await self._session.get(ProviderEngagementDocumentModel, entity.id.value)
        if existing is None:
            self._session.add(model)
        else:
            existing.state = model.state
            existing.note = model.note
            existing.updated_at = model.updated_at
        await self._session.flush()
