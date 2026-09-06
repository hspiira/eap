"""Bulk resolution of the organisation behind a session's own affiliation."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.session_attribution_reader import SessionAttributionReader
from app.domain.value_objects.core import TenantId
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel


class SqlSessionAttributionReader(SessionAttributionReader):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def organisation_ids_by_affiliation(
        self, tenant_id: TenantId, affiliation_ids: Sequence[str]
    ) -> dict[str, str]:
        wanted = {value for value in affiliation_ids if value}
        if not wanted:
            return {}
        result = await self.session.execute(
            select(ProviderAffiliationModel.id, ProviderAffiliationModel.organisation_id).where(
                ProviderAffiliationModel.tenant_id == tenant_id.value,
                ProviderAffiliationModel.id.in_(wanted),
            )
        )
        return {row.id: row.organisation_id for row in result}
