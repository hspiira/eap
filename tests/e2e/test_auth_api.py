"""
End-to-end cover for /auth — login, refresh, logout, /me.

auth.py is 638 lines of the most security-critical logic in the service (login,
lockout, token rotation, revocation, cookies, SSO) and had no e2e coverage at
all. Like the cross-tenant module, these run against the real dependencies: only
get_db is overridden, so the guards, the rate limiter and the lockout policy are
the real ones.
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

TENANT = "tenant-auth-e2e"
CODE = "auth-e2e"
EMAIL = "authuser@example.test"
PASSWORD = "correct-horse-battery-staple"
USER = "user-auth-e2e"


@pytest_asyncio.fixture
async def auth_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Only get_db is overridden — the auth stack itself is real."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # The per-IP login limiter is in-process and every test shares one fake IP;
    # without a fresh backend the file 429s itself partway through.
    app.state.login_rate_limit_backend = MemoryLoginRateLimitBackend()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded(db_session: AsyncSession) -> AsyncGenerator[None, None]:
    """An active tenant with one active, password-bearing user."""
    pw = hash_password(PASSWORD)
    stmts = [
        f"DELETE FROM users WHERE tenant_id = '{TENANT}'",
        f"DELETE FROM tenants WHERE id = '{TENANT}'",
        f"INSERT INTO tenants (id,name,code,status,settings,subscription_tier,created_at,updated_at)"
        f" VALUES ('{TENANT}','Auth E2E','{CODE}','Active','{{}}','Professional',now(),now())",
        f"INSERT INTO users (id,tenant_id,email,password_hash,status,role,is_two_factor_enabled,"
        f" failed_login_count,created_at,updated_at)"
        f" VALUES ('{USER}','{TENANT}','{EMAIL}','{pw}','Active','Admin',false,0,now(),now())",
    ]
    for s in stmts:
        await db_session.execute(text(s))
    await db_session.commit()
    yield


def _login(email: str = EMAIL, password: str = PASSWORD, code: str = CODE) -> dict[str, str]:
    return {"tenant_code": code, "email": email, "password": password}


class TestLogin:
    async def test_valid_credentials_return_tokens(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        r = await auth_client.post("/auth/login", json=_login())
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    async def test_wrong_password_is_401(self, auth_client: AsyncClient, seeded: Any) -> None:
        r = await auth_client.post("/auth/login", json=_login(password="wrong"))
        assert r.status_code == 401

    async def test_wrong_password_does_not_say_which_part_was_wrong(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        """Distinguishing a bad password from an unknown user enumerates users."""
        bad_pw = await auth_client.post("/auth/login", json=_login(password="wrong"))
        no_user = await auth_client.post("/auth/login", json=_login(email="nobody@example.test"))
        assert bad_pw.status_code == no_user.status_code == 401
        assert bad_pw.json()["message"] == no_user.json()["message"]

    async def test_unknown_tenant_is_401(self, auth_client: AsyncClient, seeded: Any) -> None:
        r = await auth_client.post("/auth/login", json=_login(code="no-such"))
        assert r.status_code == 401

    async def test_token_carries_the_users_tenant(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        """The whole tenancy model rests on this claim being right."""
        r = await auth_client.post("/auth/login", json=_login())
        token = r.json()["access_token"]
        me = await auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["tenant_id"] == TENANT
        assert me.json()["user_id"] == USER


class TestSuspendedTenant:
    async def test_login_is_refused_when_the_tenant_is_not_active(
        self, auth_client: AsyncClient, seeded: Any, db_session: AsyncSession
    ) -> None:
        await db_session.execute(
            text(f"UPDATE tenants SET status = 'Suspended' WHERE id = '{TENANT}'")
        )
        await db_session.commit()
        r = await auth_client.post("/auth/login", json=_login())
        assert r.status_code == 403, r.text[:200]


class TestLockout:
    """
    Two independent defences fire at the same count (5): the per-IP login rate
    limiter, checked first, and the per-account lockout. From one IP the limiter
    always wins, so the lockout only does real work against attempts spread over
    many IPs — which is exactly the case the limiter cannot catch. These tests
    come through both doors.
    """

    async def test_repeated_failures_from_one_ip_are_rate_limited(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        for _ in range(6):
            r = await auth_client.post("/auth/login", json=_login(password="wrong"))
        assert r.status_code in (429, 423)

    async def test_failures_spread_across_ips_still_lock_the_account(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        """The distributed case: the IP limiter is useless, the lockout is not."""
        from app.core.config import settings

        for i in range(settings.LOGIN_LOCKOUT_THRESHOLD):
            r = await auth_client.post(
                "/auth/login",
                json=_login(password="wrong"),
                headers={"X-Forwarded-For": f"10.0.0.{i + 1}"},
            )
            assert r.status_code == 401, f"attempt {i} was {r.status_code}, expected 401"

        # A fresh IP, and the right password: the account itself must be locked.
        r = await auth_client.post(
            "/auth/login", json=_login(), headers={"X-Forwarded-For": "10.0.0.99"}
        )
        assert r.status_code == 423, (
            f"correct password accepted after {settings.LOGIN_LOCKOUT_THRESHOLD} "
            f"failures: {r.status_code}"
        )

    async def test_a_successful_login_does_not_lock(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        for i in range(3):
            r = await auth_client.post(
                "/auth/login", json=_login(), headers={"X-Forwarded-For": f"10.1.0.{i + 1}"}
            )
            assert r.status_code == 200


class TestMe:
    async def test_requires_a_token(self, auth_client: AsyncClient, seeded: Any) -> None:
        assert (await auth_client.get("/auth/me")).status_code == 401

    async def test_rejects_a_garbage_token(self, auth_client: AsyncClient, seeded: Any) -> None:
        r = await auth_client.get("/auth/me", headers={"Authorization": "Bearer nope"})
        assert r.status_code == 401

    async def test_returns_email_and_role_from_the_db(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        token = (await auth_client.post("/auth/login", json=_login())).json()["access_token"]
        r = await auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.json()["email"] == EMAIL
        assert r.json()["role"] == "Admin"


class TestRefresh:
    async def test_a_refresh_token_buys_a_new_access_token(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        rt = (await auth_client.post("/auth/login", json=_login())).json()["refresh_token"]
        r = await auth_client.post("/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 200, r.text[:300]
        assert r.json()["access_token"]

    async def test_an_access_token_is_not_a_refresh_token(
        self, auth_client: AsyncClient, seeded: Any
    ) -> None:
        """Tokens are type-tagged; using the wrong one must not work."""
        at = (await auth_client.post("/auth/login", json=_login())).json()["access_token"]
        r = await auth_client.post("/auth/refresh", json={"refresh_token": at})
        assert r.status_code == 401

    async def test_garbage_is_rejected(self, auth_client: AsyncClient, seeded: Any) -> None:
        r = await auth_client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
        assert r.status_code == 401
