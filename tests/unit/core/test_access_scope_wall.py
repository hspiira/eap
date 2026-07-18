"""
The clinical/employer privacy wall.

require_scope fails closed: a token with no grants is refused, full stop.
There is no legacy escape hatch — scopes are stamped at mint from the DB
user, so every valid token carries its current grants. These tests pin the
wall itself, the mint/decode roundtrip, and the platform-admin-only rule
for granting Clinical.
"""

import pytest
from fastapi import HTTPException

from app.core import authorization
from app.core.authorization import is_platform_admin, require_clinical_scope, require_scope
from app.core.security import TokenData, create_access_token, decode_token
from app.domain.enums import AccessScope


def _token(scopes: list[str], tenant_id: str = "t1") -> TokenData:
    return TokenData(
        user_id="u1", tenant_id=tenant_id, email="u@example.test", access_scopes=scopes
    )


async def _call(dep, token: TokenData) -> TokenData:
    return await dep(current_user=token)


class TestTheWallFailsClosed:
    async def test_no_grants_is_refused(self) -> None:
        with pytest.raises(HTTPException) as e:
            await _call(require_clinical_scope, _token([]))
        assert e.value.status_code == 403

    async def test_wrong_scope_is_refused(self) -> None:
        with pytest.raises(HTTPException) as e:
            await _call(require_clinical_scope, _token([AccessScope.EMPLOYER_PORTAL.value]))
        assert e.value.status_code == 403

    async def test_clinical_grant_is_admitted(self) -> None:
        result = await _call(require_clinical_scope, _token([AccessScope.CLINICAL.value]))
        assert result is not None

    async def test_any_of_multiple_allowed_scopes_admits(self) -> None:
        dep = require_scope(AccessScope.CLINICAL, AccessScope.EMPLOYER_PORTAL)
        assert await _call(dep, _token([AccessScope.EMPLOYER_PORTAL.value])) is not None

    async def test_unknown_scope_strings_do_not_admit(self) -> None:
        """A forged or stale claim value must not slip through."""
        with pytest.raises(HTTPException):
            await _call(require_clinical_scope, _token(["Clinical-Extra", "admin", ""]))


class TestMintCarriesScopes:
    def test_roundtrip(self) -> None:
        token = create_access_token(
            user_id="u1",
            tenant_id="t1",
            access_scopes=[AccessScope.CLINICAL.value],
        )
        decoded = decode_token(token)
        assert decoded.access_scopes == [AccessScope.CLINICAL.value]

    def test_no_scopes_decodes_to_empty(self) -> None:
        token = create_access_token(user_id="u1", tenant_id="t1")
        assert decode_token(token).access_scopes == []

    def test_non_list_claim_is_ignored(self) -> None:
        token = create_access_token(
            user_id="u1", tenant_id="t1", additional_claims={"access_scopes": "Clinical"}
        )
        assert decode_token(token).access_scopes == []


class TestPlatformAdminCheck:
    def test_matching_tenant_is_platform_admin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(authorization.settings, "PLATFORM_TENANT_ID", "plat-1")
        assert is_platform_admin(_token([], tenant_id="plat-1")) is True
        assert is_platform_admin(_token([], tenant_id="other")) is False

    def test_unconfigured_platform_means_nobody(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(authorization.settings, "PLATFORM_TENANT_ID", "")
        assert is_platform_admin(_token([], tenant_id="anything")) is False
