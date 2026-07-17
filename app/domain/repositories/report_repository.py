"""Report repositories (Phase 2 #D-Reports)."""

from app.domain.entities.report import ReportRun, ReportTemplate
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    ReportRunId,
    ReportTemplateId,
    TenantId,
)


class ReportTemplateRepository(BaseRepository[ReportTemplate, ReportTemplateId]):
    async def list_for_tenant(
        self,
        tenant_id: TenantId,
        *,
        active_only: bool = True,
    ) -> list[ReportTemplate]: ...

    async def get_by_code(self, tenant_id: TenantId, code: str) -> ReportTemplate | None: ...


class ReportRunRepository(BaseRepository[ReportRun, ReportRunId]):
    async def list_for_template(
        self,
        tenant_id: TenantId,
        template_id: ReportTemplateId,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReportRun]: ...
