from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.client_use_cases import CreateClientUseCase, UpdateClientUseCase
from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ClientTier, ContactMethod
from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.value_objects.core import Address, ClientId, ContactInfo, IndustryId, TenantId


def make_client(tenant_id: str, client_id: str = "client-1") -> ClientEntity:
    now = datetime.now(UTC)
    return ClientEntity(
        id=ClientId(client_id),
        tenant_id=TenantId(tenant_id),
        name="Existing Client",
        code="OLD",
        contact_info=ContactInfo(phone="+256700000000"),
        status=BaseStatus.PENDING,
        is_verified=False,
        created_at=now,
        updated_at=now,
    )


def make_repositories() -> tuple[SimpleNamespace, SimpleNamespace]:
    client_repo = SimpleNamespace(
        get_by_name=AsyncMock(return_value=None),
        get_by_code=AsyncMock(return_value=None),
        get_by_id=AsyncMock(return_value=None),
        save=AsyncMock(),
    )
    industry_repo = SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    return client_repo, industry_repo


@pytest.mark.asyncio
async def test_create_normalizes_business_keys() -> None:
    client_repo, industry_repo = make_repositories()

    result = await CreateClientUseCase(client_repo, industry_repository=industry_repo).execute(
        client_id=ClientId("client-new"),
        tenant_id=TenantId("tenant-1"),
        name="  Acme Corporation  ",
        code=" acm ",
        contact_info=ContactInfo(phone="+256700000000"),
    )

    assert result.name == "Acme Corporation"
    assert result.code == "ACM"
    client_repo.get_by_code.assert_awaited_once()
    client_repo.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_rejects_duplicate_code() -> None:
    client_repo, industry_repo = make_repositories()
    client_repo.get_by_code.return_value = make_client("tenant-1")

    with pytest.raises(ConflictError, match="code"):
        await CreateClientUseCase(client_repo, industry_repository=industry_repo).execute(
            client_id=ClientId("client-new"),
            tenant_id=TenantId("tenant-1"),
            name="New Client",
            code="old",
            contact_info=ContactInfo(phone="+256700000000"),
        )


@pytest.mark.asyncio
async def test_create_rejects_parent_from_another_tenant() -> None:
    client_repo, industry_repo = make_repositories()
    client_repo.get_by_id.return_value = make_client("other-tenant", "parent-1")

    with pytest.raises(NotFoundError, match="Parent client"):
        await CreateClientUseCase(client_repo, industry_repository=industry_repo).execute(
            client_id=ClientId("client-new"),
            tenant_id=TenantId("tenant-1"),
            name="New Client",
            code="NEW",
            contact_info=ContactInfo(phone="+256700000000"),
            parent_client_id=ClientId("parent-1"),
        )


@pytest.mark.asyncio
async def test_create_rejects_industry_from_another_tenant() -> None:
    client_repo, industry_repo = make_repositories()
    industry_repo.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId("other-tenant"))

    with pytest.raises(NotFoundError, match="Industry"):
        await CreateClientUseCase(client_repo, industry_repository=industry_repo).execute(
            client_id=ClientId("client-new"),
            tenant_id=TenantId("tenant-1"),
            name="New Client",
            code="NEW",
            contact_info=ContactInfo(phone="+256700000000"),
            industry_id=IndustryId("industry-1"),
        )


@pytest.mark.asyncio
async def test_update_persists_profile_fields_atomically() -> None:
    client_repo, industry_repo = make_repositories()
    existing = make_client("tenant-1")
    client_repo.get_by_id.return_value = existing
    industry_repo.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId("tenant-1"))

    result = await UpdateClientUseCase(client_repo).execute(
        existing.id,
        name="Updated Client",
        preferred_contact_method=ContactMethod.EMAIL,
        tier=ClientTier.A,
        contact_info=ContactInfo(phone="+256711111111"),
        billing_address=Address(street="1 Main", city="Kampala", country="Uganda"),
        industry_id=IndustryId("industry-1"),
        industry_repository=industry_repo,
    )

    assert result.name == "Updated Client"
    assert result.preferred_contact_method == ContactMethod.EMAIL
    assert result.tier == ClientTier.A
    assert result.contact_info.phone == "+256711111111"
    assert result.billing_address is not None
    assert result.industry_id == IndustryId("industry-1")
    client_repo.save.assert_awaited_once_with(existing)
