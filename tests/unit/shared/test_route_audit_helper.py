"""
audit_change defaulting.

128 of 153 call sites rely on tenant_id defaulting to the entity's own, and on
user_id being read off current_user. The 25 that can't (tenants, where the entity
*is* the tenant) pass tenant_id explicitly. Both paths are pinned here.
"""

from types import SimpleNamespace
from typing import Any

import pytest

from app.shared.utils import route_audit_helper
from app.shared.utils.route_audit_helper import audit_change


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    async def fake(**kwargs: Any) -> None:
        seen.update(kwargs)

    monkeypatch.setattr(route_audit_helper, "audit_entity_operation", fake)
    return seen


ENTITY = SimpleNamespace(id="e1", tenant_id="t-own")
USER = SimpleNamespace(user_id="u1")


class TestDefaults:
    async def test_tenant_id_defaults_to_the_entitys_own(
        self, captured: dict[str, Any]
    ) -> None:
        await audit_change(ENTITY, "handler", USER, "request")
        assert captured["tenant_id"] == "t-own"

    async def test_user_id_is_read_off_current_user(
        self, captured: dict[str, Any]
    ) -> None:
        await audit_change(ENTITY, "handler", USER, "request")
        assert captured["user_id"] == "u1"

    async def test_entity_handler_and_request_pass_through(
        self, captured: dict[str, Any]
    ) -> None:
        await audit_change(ENTITY, "handler", USER, "request")
        assert captured["entity"] is ENTITY
        assert captured["audit_handler"] == "handler"
        assert captured["request"] == "request"


class TestOverrides:
    async def test_explicit_tenant_id_wins(self, captured: dict[str, Any]) -> None:
        """The tenants route passes tenant.id, since the entity is the tenant."""
        await audit_change(ENTITY, "handler", USER, "request", tenant_id="t-explicit")
        assert captured["tenant_id"] == "t-explicit"

    async def test_no_current_user_yields_no_user_id(
        self, captured: dict[str, Any]
    ) -> None:
        """Tenant self-registration audits with no authenticated user."""
        await audit_change(ENTITY, "handler", None, "request")
        assert captured["user_id"] is None

    async def test_old_entity_and_db_pass_through(self, captured: dict[str, Any]) -> None:
        await audit_change(ENTITY, "handler", USER, "request", old_entity="old", db="db")
        assert captured["old_entity"] == "old"
        assert captured["db"] == "db"
