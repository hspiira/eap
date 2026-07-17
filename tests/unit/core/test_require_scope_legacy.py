"""
The legacy-token escape hatch in require_scope.

A token minted before the scope rollout carries no access_scopes claim and is
admitted regardless of the route's scopes — it bypasses the scope wall entirely.
That is deliberate and transitional, and it is governed by
SCOPE_FAIL_CLOSED_ON_LEGACY so the cutover is a config change per environment.

These pin both sides, so the day someone flips the flag they already know what
it does. See §4 of 11_RELEASE_RUNBOOK_AND_OPEN_ACTIONS.md.
"""

import pytest
from fastapi import HTTPException

from app.core import authorization
from app.core.authorization import require_scope
from app.core.security import TokenData
from app.domain.enums import AccessScope

SCOPE = next(iter(AccessScope))
OTHER = [s for s in AccessScope if s is not SCOPE]


def _token(scopes: list[str]) -> TokenData:
    """A legacy token is an empty scopes list — TokenData does not allow None."""
    return TokenData(
        user_id="u1", tenant_id="t1", email="u@example.test", access_scopes=scopes
    )


async def _call(dep, token: TokenData) -> TokenData:
    return await dep(current_user=token)


class TestLegacyTokensOpenByDefault:
    """Today's behaviour: no claim means no check."""

    async def test_a_token_with_no_scopes_is_admitted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(authorization.settings, "SCOPE_FAIL_CLOSED_ON_LEGACY", False)
        assert await _call(require_scope(SCOPE), _token([])) is not None

    async def test_the_default_setting_is_open(self) -> None:
        """Pinning today's default, so the cutover is a visible change."""
        from app.core.config import Settings

        assert Settings.model_fields["SCOPE_FAIL_CLOSED_ON_LEGACY"].default is False


class TestTheCutover:
    """What flipping SCOPE_FAIL_CLOSED_ON_LEGACY will do."""

    async def test_a_legacy_token_is_then_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(authorization.settings, "SCOPE_FAIL_CLOSED_ON_LEGACY", True)
        with pytest.raises(HTTPException) as e:
            await _call(require_scope(SCOPE), _token([]))
        assert e.value.status_code == 403

    async def test_a_scoped_token_still_works(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The cutover must not break tokens that did the right thing."""
        monkeypatch.setattr(authorization.settings, "SCOPE_FAIL_CLOSED_ON_LEGACY", True)
        assert await _call(require_scope(SCOPE), _token([SCOPE.value])) is not None


class TestScopeCheckingItself:
    """Unaffected by the flag — a wrong scope is always wrong."""

    @pytest.mark.parametrize("flag", [True, False])
    async def test_a_token_with_the_wrong_scope_is_refused(
        self, monkeypatch: pytest.MonkeyPatch, flag: bool
    ) -> None:
        if not OTHER:
            pytest.skip("only one AccessScope defined")
        monkeypatch.setattr(authorization.settings, "SCOPE_FAIL_CLOSED_ON_LEGACY", flag)
        with pytest.raises(HTTPException) as e:
            await _call(require_scope(SCOPE), _token([OTHER[0].value]))
        assert e.value.status_code == 403

    @pytest.mark.parametrize("flag", [True, False])
    async def test_the_per_route_override_still_wins(
        self, monkeypatch: pytest.MonkeyPatch, flag: bool
    ) -> None:
        monkeypatch.setattr(authorization.settings, "SCOPE_FAIL_CLOSED_ON_LEGACY", flag)
        with pytest.raises(HTTPException):
            await _call(require_scope(SCOPE, fail_closed_on_legacy=True), _token([]))
