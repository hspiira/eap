"""
End-to-end cover for the clinical privacy wall.

Runs against the real auth stack (only get_db is overridden): a real login
mints the access_scopes claim from the DB user, and the clinical routes
admit or refuse on it. This is the product's core privacy promise: an
employer's HR admin must never see clinical data, so it gets its own
e2e module rather than riding along in another file.
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
from app.core.login_rate_limit import MemoryLoginRateLimitBackend  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402

TENANT = "tenant-scope-e2e"
CODE = "scope-e2e"
PASSWORD = "correct-horse-battery-staple"
HR_EMAIL = "hradmin@example.test"
COUNSELLOR_EMAIL = "counsellor@example.test"


@pytest_asyncio.fixture
async def wall_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Only get_db is overridden; auth, minting and the wall are real."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.state.login_rate_limit_backend = MemoryLoginRateLimitBackend()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded(db_session: AsyncSession) -> AsyncGenerator[None, None]:
    """One tenant, two users: an HR admin (no grants) and a counsellor (Clinical)."""
    pw = hash_password(PASSWORD)
    stmts = [
        f"DELETE FROM users WHERE tenant_id = '{TENANT}'",
        f"DELETE FROM tenants WHERE id = '{TENANT}'",
        f"INSERT INTO tenants (id,name,code,status,settings,subscription_tier,created_at,updated_at)"
        f" VALUES ('{TENANT}','Scope E2E','{CODE}','Active','{{}}','Professional',now(),now())",
        f"INSERT INTO users (id,tenant_id,email,password_hash,status,role,is_two_factor_enabled,"
        f" failed_login_count,access_scopes,created_at,updated_at)"
        f" VALUES ('user-hr-e2e','{TENANT}','{HR_EMAIL}','{pw}','Active','Admin',false,0,'[]',now(),now())",
        f"INSERT INTO users (id,tenant_id,email,password_hash,status,role,is_two_factor_enabled,"
        f" failed_login_count,access_scopes,created_at,updated_at)"
        f" VALUES ('user-couns-e2e','{TENANT}','{COUNSELLOR_EMAIL}','{pw}','Active','User',false,0,"
        f" '[\"Clinical\"]',now(),now())",
    ]
    for s in stmts:
        await db_session.execute(text(s))
    await db_session.commit()
    yield


async def _login(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/auth/login", json={"tenant_code": CODE, "email": email, "password": PASSWORD}
    )
    assert r.status_code == 200, r.text[:300]
    return r.json()["access_token"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestTheWall:
    async def test_hr_admin_cannot_list_cases(self, wall_client: AsyncClient, seeded: Any) -> None:
        """Tenant ADMIN role does not imply clinical access, the whole point."""
        token = await _login(wall_client, HR_EMAIL)
        r = await wall_client.get(f"/cases?tenant_id={TENANT}", headers=_bearer(token))
        assert r.status_code == 403

    async def test_counsellor_can_list_cases(self, wall_client: AsyncClient, seeded: Any) -> None:
        token = await _login(wall_client, COUNSELLOR_EMAIL)
        r = await wall_client.get(f"/cases?tenant_id={TENANT}", headers=_bearer(token))
        assert r.status_code == 200

    async def test_hr_admin_cannot_read_clinical_notes(
        self, wall_client: AsyncClient, seeded: Any
    ) -> None:
        token = await _login(wall_client, HR_EMAIL)
        r = await wall_client.get(
            f"/cases/some-case-id/clinical-notes?tenant_id={TENANT}", headers=_bearer(token)
        )
        assert r.status_code == 403

    async def test_me_reports_the_grants(self, wall_client: AsyncClient, seeded: Any) -> None:
        """The FE decides what to render from /auth/me; it must see the grants."""
        token = await _login(wall_client, COUNSELLOR_EMAIL)
        r = await wall_client.get("/auth/me", headers=_bearer(token))
        assert r.status_code == 200
        assert r.json()["access_scopes"] == ["Clinical"]

        token_hr = await _login(wall_client, HR_EMAIL)
        r_hr = await wall_client.get("/auth/me", headers=_bearer(token_hr))
        assert r_hr.json()["access_scopes"] == []


    async def test_dashboard_outcome_mix_follows_the_wall(
        self, wall_client: AsyncClient, seeded: Any
    ) -> None:
        """The aggregate outcome mix is clinical data like any other.

        A counsellor gets the block (a list, possibly empty); HR gets null in
        the same 200 response, not a 403, because the rest of the dashboard is
        theirs to see.
        """
        token = await _login(wall_client, COUNSELLOR_EMAIL)
        r = await wall_client.get(f"/dashboard?tenant_id={TENANT}", headers=_bearer(token))
        assert r.status_code == 200, r.text[:300]
        assert isinstance(r.json()["outcome_mix"], list)

        token_hr = await _login(wall_client, HR_EMAIL)
        r_hr = await wall_client.get(f"/dashboard?tenant_id={TENANT}", headers=_bearer(token_hr))
        assert r_hr.status_code == 200
        assert r_hr.json()["outcome_mix"] is None


class TestGrantRules:
    async def test_tenant_admin_cannot_grant_clinical(
        self, wall_client: AsyncClient, seeded: Any
    ) -> None:
        """Employers cannot quietly grant themselves the PHI scope."""
        token = await _login(wall_client, HR_EMAIL)
        r = await wall_client.patch(
            f"/users/user-hr-e2e/access-scopes?tenant_id={TENANT}",
            json={"access_scopes": ["Clinical"]},
            headers=_bearer(token),
        )
        assert r.status_code == 403

    async def test_tenant_admin_can_grant_employer_portal(
        self, wall_client: AsyncClient, seeded: Any
    ) -> None:
        token = await _login(wall_client, HR_EMAIL)
        r = await wall_client.patch(
            f"/users/user-hr-e2e/access-scopes?tenant_id={TENANT}",
            json={"access_scopes": ["EmployerPortal"]},
            headers=_bearer(token),
        )
        assert r.status_code == 200, r.text[:300]
        assert r.json()["access_scopes"] == ["EmployerPortal"]

    async def test_a_fresh_login_picks_up_new_grants(
        self, wall_client: AsyncClient, seeded: Any, db_session: AsyncSession
    ) -> None:
        """Grants live in the DB; the next mint carries them."""
        await db_session.execute(
            text("UPDATE users SET access_scopes = '[\"Clinical\"]' WHERE id = 'user-hr-e2e'")
        )
        await db_session.commit()
        token = await _login(wall_client, HR_EMAIL)
        r = await wall_client.get(f"/cases?tenant_id={TENANT}", headers=_bearer(token))
        assert r.status_code == 200
