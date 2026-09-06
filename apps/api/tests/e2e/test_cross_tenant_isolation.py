"""
Cross-tenant isolation, exercised against the real authorization guards.

The rest of the e2e suite cannot test this. `tests/conftest.py` overrides
`get_current_user` to echo back whatever `tenant_id` the request asks for
("so require_same_tenant passes"), and overrides `get_user_in_tenant` to skip
the tenant check outright ("so existing E2E tests pass"). Every guard therefore
succeeds by construction, and the highest-risk bug class in a multi-tenant
health product (one tenant reading another's data) is untestable.

These tests mint real JWTs for two tenants and override only the database, so
`require_same_tenant` and friends run for real.
"""

import os

os.environ["ENVIRONMENT"] = "test"

from collections.abc import AsyncGenerator  # noqa: E402
from typing import Any  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402

TENANT_A = "tenant-iso-a"
TENANT_B = "tenant-iso-b"
CLIENT_B = "client-iso-b"


def _auth(tenant_id: str, user_id: str) -> dict[str, str]:
    """A real signed token, not the conftest override."""
    token = create_access_token(
        user_id=user_id, tenant_id=tenant_id, email=f"{user_id}@example.com"
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def isolated_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Client with only `get_db` overridden. The authorization guards are the real
    ones, which is the entire point of this module.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def two_tenants(db_session: AsyncSession) -> AsyncGenerator[None, None]:
    """Two tenants; only B owns a client."""
    stmts = [
        f"INSERT INTO tenants (id,name,code,status,settings,subscription_tier,created_at,updated_at)"
        f" VALUES ('{TENANT_A}','Iso A','iso-a','Active','{{}}','Professional',now(),now())"
        f" ON CONFLICT (id) DO NOTHING",
        f"INSERT INTO tenants (id,name,code,status,settings,subscription_tier,created_at,updated_at)"
        f" VALUES ('{TENANT_B}','Iso B','iso-b','Active','{{}}','Professional',now(),now())"
        f" ON CONFLICT (id) DO NOTHING",
        f"INSERT INTO clients (id,tenant_id,name,code,status,contact_info,is_verified,created_at,updated_at)"
        f" VALUES ('{CLIENT_B}','{TENANT_B}','B Client','BCL','Active','{{}}',false,now(),now())"
        f" ON CONFLICT (id) DO NOTHING",
    ]
    for s in stmts:
        await db_session.execute(text(s))
    await db_session.commit()
    yield


class TestTenantScopedReads:
    """A token for tenant A must not reach tenant B's data."""

    async def test_cannot_list_another_tenants_clients(
        self, isolated_client: AsyncClient, two_tenants: Any
    ) -> None:
        r = await isolated_client.get(
            "/clients/", params={"tenant_id": TENANT_B}, headers=_auth(TENANT_A, "u-a")
        )
        assert r.status_code in (401, 403), (
            f"tenant A listed tenant B's clients: {r.status_code} {r.text[:200]}"
        )

    async def test_can_list_own_clients(
        self, isolated_client: AsyncClient, two_tenants: Any
    ) -> None:
        """The guard must not be so blunt it blocks legitimate access."""
        r = await isolated_client.get(
            "/clients/", params={"tenant_id": TENANT_B}, headers=_auth(TENANT_B, "u-b")
        )
        assert r.status_code == 200, f"tenant B blocked from its own clients: {r.text[:200]}"

    async def test_cannot_read_another_tenants_client_by_id(
        self, isolated_client: AsyncClient, two_tenants: Any
    ) -> None:
        r = await isolated_client.get(
            f"/clients/{CLIENT_B}",
            params={"tenant_id": TENANT_A},
            headers=_auth(TENANT_A, "u-a"),
        )
        # 404 is as acceptable as 403; it leaks less.
        assert r.status_code in (401, 403, 404), (
            f"tenant A read tenant B's client: {r.status_code} {r.text[:200]}"
        )

    async def test_members_ignore_a_supplied_tenant_id(
        self, isolated_client: AsyncClient, two_tenants: Any
    ) -> None:
        """`/members` takes no tenant_id: it reads the caller's token instead.

        Replaces the `/persons` case this class used to cover. That router was
        retired with the members migration, so the assertion had stopped
        exercising anything. The property here is different from the clients
        one above by design: rather than rejecting another tenant's id, the
        endpoint has no parameter to reject, so naming one changes nothing.
        """
        headers = _auth(TENANT_A, "u-a")
        own = await isolated_client.get("/members", headers=headers)
        spoofed = await isolated_client.get(
            "/members", params={"tenant_id": TENANT_B}, headers=headers
        )
        assert own.status_code == 200
        assert spoofed.status_code == 200
        assert spoofed.json()["total"] == own.json()["total"]


class TestUnauthenticated:
    async def test_no_token_is_rejected(
        self, isolated_client: AsyncClient, two_tenants: Any
    ) -> None:
        r = await isolated_client.get("/clients/", params={"tenant_id": TENANT_B})
        assert r.status_code == 401

    async def test_garbage_token_is_rejected(
        self, isolated_client: AsyncClient, two_tenants: Any
    ) -> None:
        r = await isolated_client.get(
            "/clients/",
            params={"tenant_id": TENANT_B},
            headers={"Authorization": "Bearer not-a-jwt"},
        )
        assert r.status_code == 401


class TestTenantScopedWrites:
    async def test_cannot_create_a_client_in_another_tenant(
        self, isolated_client: AsyncClient, two_tenants: Any
    ) -> None:
        r = await isolated_client.post(
            "/clients/",
            params={"tenant_id": TENANT_B},
            headers=_auth(TENANT_A, "u-a"),
            json={"name": "Smuggled", "code": "SMUG", "contact_info": {}},
        )
        assert r.status_code in (401, 403), (
            f"tenant A created a client in tenant B: {r.status_code} {r.text[:200]}"
        )
