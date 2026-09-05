"""Client tier (A/B/C) tests (Phase 2 #D-Tier)."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ClientTier
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ClientId, ContactInfo, Email, TenantId


def _client(
    *, status: BaseStatus = BaseStatus.ACTIVE, tier: ClientTier | None = None
) -> ClientEntity:
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
        c.update_tier(ClientTier.A)
        assert c.tier == ClientTier.A

    def test_can_change_tier(self):
        c = _client(tier=ClientTier.A)
        c.update_tier(ClientTier.B)
        assert c.tier == ClientTier.B

    def test_can_clear_tier(self):
        c = _client(tier=ClientTier.B)
        c.update_tier(None)
        assert c.tier is None

    def test_update_refreshes_timestamp(self):
        c = _client()
        before = c.updated_at
        c.update_tier(ClientTier.C)
        assert c.updated_at >= before

    def test_cannot_update_when_deleted(self):
        c = _client(status=BaseStatus.DELETED)
        with pytest.raises(DomainError):
            c.update_tier(ClientTier.A)

    @pytest.mark.parametrize("tier", [ClientTier.A, ClientTier.B, ClientTier.C])
    def test_all_tiers_accepted(self, tier: ClientTier):
        c = _client()
        c.update_tier(tier)
        assert c.tier == tier
