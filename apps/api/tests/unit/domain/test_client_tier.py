"""Client tier (A/B/C) tests (Phase 2 #D-Tier)."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ClientId, ContactInfo, Email, TenantId


def _client(*, status: BaseStatus = BaseStatus.ACTIVE, tier: str | None = None) -> ClientEntity:
    now = datetime.now(UTC)
    return ClientEntity(
        id=ClientId("c-1"),
        tenant_id=TenantId("t-1"),
        name="ACME",
        code="ACM",
        contact_info=ContactInfo(phone="+254700000000", email=Email("ops@acme.example")),
        status=status,
        is_verified=True,
        created_at=now,
        updated_at=now,
        tier=tier,
    )


class TestClientTier:
    def test_default_is_none(self):
        assert _client().tier is None

    def test_can_set_tier_a(self):
        c = _client()
        c.update_tier("A")
        assert c.tier == "A"

    def test_can_change_tier(self):
        c = _client(tier="A")
        c.update_tier("B")
        assert c.tier == "B"

    def test_can_clear_tier(self):
        c = _client(tier="B")
        c.update_tier(None)
        assert c.tier is None

    def test_update_refreshes_timestamp(self):
        c = _client()
        before = c.updated_at
        c.update_tier("C")
        assert c.updated_at >= before

    def test_cannot_update_when_deleted(self):
        c = _client(status=BaseStatus.DELETED)
        with pytest.raises(DomainError):
            c.update_tier("A")

    @pytest.mark.parametrize("tier", ["A", "B", "C"])
    def test_all_tiers_accepted(self, tier: str):
        c = _client()
        c.update_tier(tier)
        assert c.tier == tier
