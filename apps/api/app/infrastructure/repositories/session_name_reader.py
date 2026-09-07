"""Bulk name resolution for the session list, one query per entity kind."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.session_name_reader import SessionNameReader, SessionNames
from app.domain.value_objects.core import TenantId
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.service_model import ServiceModel


class SqlSessionNameReader(SessionNameReader):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _names(self, model, name_column, tenant_id: str, ids: Sequence[str]):
        wanted = {value for value in ids if value}
        if not wanted:
            return {}
        result = await self.session.execute(
            select(model.id, name_column).where(
                model.tenant_id == tenant_id,
                model.id.in_(wanted),
            )
        )
        return {row[0]: row[1] for row in result if row[1]}

    async def names_for(
        self,
        tenant_id: TenantId,
        *,
        client_ids: Sequence[str],
        member_ids: Sequence[str],
        provider_ids: Sequence[str],
        service_ids: Sequence[str],
    ) -> SessionNames:
        tenant = tenant_id.value
        return SessionNames(
            clients=await self._names(ClientModel, ClientModel.name, tenant, client_ids),
            members=await self._names(
                EligibleMemberModel, EligibleMemberModel.display_label, tenant, member_ids
            ),
            providers=await self._names(
                ProviderModel, ProviderModel.display_name, tenant, provider_ids
            ),
            services=await self._names(ServiceModel, ServiceModel.name, tenant, service_ids),
        )
