"""
Azure identity linking invariants on UserEntity.

The SSO callback resolves a user by Azure OID and falls back to email. Without a
guard on re-linking, an email address recycled by the customer's IT department
(offboard A, later reassign the address to new hire B) would let B's first SSO
login silently inherit A's account: role, access scopes, case history, audit
identity. In an EAP system holding PHI that is an access-control failure, so the
invariant lives on the entity rather than in one caller.
"""

from datetime import UTC, datetime

import pytest

from app.domain.entities.user import UserEntity
from app.domain.enums import AuthProvider, UserStatus
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import Email, TenantId, UserId


@pytest.fixture
def user() -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        id=UserId("user-123"),
        tenant_id=TenantId("tenant-456"),
        email=Email("fred@minet.co.ug"),
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


class TestLinkAzureIdentity:
    def test_links_unlinked_user(self, user):
        user.link_azure_identity("oid-aaa")
        assert user.azure_oid == "oid-aaa"
        assert user.auth_provider == AuthProvider.AZURE_AD

    def test_strips_whitespace(self, user):
        user.link_azure_identity("  oid-aaa  ")
        assert user.azure_oid == "oid-aaa"

    def test_relinking_same_oid_is_idempotent(self, user):
        """Retried or concurrent logins must not fail."""
        user.link_azure_identity("oid-aaa")
        user.link_azure_identity("oid-aaa")
        assert user.azure_oid == "oid-aaa"

    def test_refuses_relink_to_different_identity(self, user):
        """The recycled-email account-takeover case."""
        user.link_azure_identity("oid-aaa")
        with pytest.raises(DomainError, match="already linked to a different Azure identity"):
            user.link_azure_identity("oid-bbb")

    def test_refused_relink_leaves_original_intact(self, user):
        """A rejected attempt must not partially mutate the account."""
        user.link_azure_identity("oid-aaa")
        with pytest.raises(DomainError):
            user.link_azure_identity("oid-bbb")
        assert user.azure_oid == "oid-aaa"

    @pytest.mark.parametrize("bad", ["", "   "])
    def test_rejects_empty_oid(self, user, bad):
        with pytest.raises(DomainError, match="cannot be empty"):
            user.link_azure_identity(bad)

    def test_rejects_deleted_user(self, user):
        user.deleted_at = datetime.now(UTC)
        with pytest.raises(DomainError, match="deleted user"):
            user.link_azure_identity("oid-aaa")
