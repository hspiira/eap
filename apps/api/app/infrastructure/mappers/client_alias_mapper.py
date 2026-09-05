"""Client alias persistence mapper."""

from app.domain.entities.client_alias import ClientAliasEntity
from app.domain.value_objects.core import ClientAliasId, ClientId, TenantId
from app.infrastructure.models.client_alias_model import ClientAliasModel
from app.shared.utils.datetime import ensure_utc


class ClientAliasMapper:
    """Convert client alias persistence models to domain entities."""

    @staticmethod
    def to_entity(model: ClientAliasModel) -> ClientAliasEntity:
        return ClientAliasEntity(
            id=ClientAliasId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=ClientId(model.client_id),
            alias=model.alias,
            normalized_alias=model.normalized_alias,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: ClientAliasEntity) -> ClientAliasModel:
        return ClientAliasModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id.value,
            alias=entity.alias,
            normalized_alias=entity.normalized_alias,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
