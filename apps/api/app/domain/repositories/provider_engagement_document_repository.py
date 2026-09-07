"""Repository port for the practitioner engagement-document checklist."""

from abc import ABC, abstractmethod

from app.domain.entities.provider_engagement_document import ProviderEngagementDocument
from app.domain.enums import EngagementDocumentKind
from app.domain.value_objects.ids import ProviderId, TenantId


class ProviderEngagementDocumentRepository(ABC):
    @abstractmethod
    async def get_for_kind(
        self, tenant_id: TenantId, provider_id: ProviderId, kind: EngagementDocumentKind
    ) -> ProviderEngagementDocument | None: ...

    @abstractmethod
    async def list_for_provider(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> list[ProviderEngagementDocument]: ...

    @abstractmethod
    async def save(self, entity: ProviderEngagementDocument) -> None: ...
