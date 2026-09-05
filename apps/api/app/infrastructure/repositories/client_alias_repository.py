"""SQLAlchemy repository for normalized client aliases."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select

from app.domain.entities.client_alias import ClientAliasEntity
from app.domain.repositories.client_alias_repository import ClientAliasRepository
from app.domain.value_objects.core import ClientAliasId, ClientId, TenantId
from app.infrastructure.mappers.client_alias_mapper import ClientAliasMapper
from app.infrastructure.models.client_alias_model import ClientAliasModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl
from app.shared.utils.client_alias import normalize_client_alias
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class ClientAliasRepositoryImpl(
    TenantScopedRepositoryImpl[ClientAliasEntity, ClientAliasModel, ClientAliasId],
    ClientAliasRepository,
):
    """Tenant-scoped alias persistence with normalized uniqueness."""

    model_class = ClientAliasModel
    id_column = "id"

    def _to_entity(self, model: ClientAliasModel) -> ClientAliasEntity:
        return ClientAliasMapper.to_entity(model)

    def _to_model(self, entity: ClientAliasEntity) -> ClientAliasModel:
        return ClientAliasMapper.to_model(entity)

    def _get_id_value(self, entity_id: ClientAliasId) -> Any:
        return entity_id.value

    async def list_for_client(
        self, client_id: ClientId, tenant_id: TenantId
    ) -> Sequence[ClientAliasEntity]:
        result = await self.session.execute(
            select(ClientAliasModel)
            .where(
                ClientAliasModel.client_id == client_id.value,
                ClientAliasModel.tenant_id == tenant_id.value,
            )
            .order_by(ClientAliasModel.alias.asc())
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def find_by_normalized(
        self, tenant_id: TenantId, normalized_alias: str
    ) -> ClientAliasEntity | None:
        result = await self.session.execute(
            select(ClientAliasModel).where(
                ClientAliasModel.tenant_id == tenant_id.value,
                ClientAliasModel.normalized_alias == normalized_alias,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def replace_for_client(
        self, client_id: ClientId, tenant_id: TenantId, aliases: Sequence[str]
    ) -> Sequence[ClientAliasEntity]:
        await self.session.execute(
            delete(ClientAliasModel).where(
                ClientAliasModel.client_id == client_id.value,
                ClientAliasModel.tenant_id == tenant_id.value,
            )
        )
        now = utc_now()
        seen: set[str] = set()
        models: list[ClientAliasModel] = []
        for alias in aliases:
            cleaned = " ".join(alias.split())
            normalized = normalize_client_alias(cleaned)
            if not cleaned or not normalized or normalized in seen:
                continue
            seen.add(normalized)
            models.append(
                ClientAliasModel(
                    id=generate_cuid(),
                    tenant_id=tenant_id.value,
                    client_id=client_id.value,
                    alias=cleaned,
                    normalized_alias=normalized,
                    created_at=now,
                    updated_at=now,
                )
            )
        self.session.add_all(models)
        await self.session.flush()
        return [self._to_entity(model) for model in models]

    async def merge_into(
        self, target_client_id: ClientId, source_client_id: ClientId, tenant_id: TenantId
    ) -> Sequence[ClientAliasEntity]:
        if target_client_id == source_client_id:
            raise ValueError("A client cannot merge aliases into itself")
        source = list(await self.list_for_client(source_client_id, tenant_id))
        target = list(await self.list_for_client(target_client_id, tenant_id))
        existing = {alias.normalized_alias for alias in target}
        for alias in source:
            model = await self.session.get(ClientAliasModel, alias.id.value)
            if not model:
                continue
            if alias.normalized_alias in existing:
                await self.session.delete(model)
            else:
                model.client_id = target_client_id.value
                existing.add(alias.normalized_alias)
        await self.session.flush()
        return await self.list_for_client(target_client_id, tenant_id)
