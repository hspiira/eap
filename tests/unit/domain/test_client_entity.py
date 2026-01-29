"""
Unit tests for ClientEntity domain entity.

Tests domain logic and invariants without database dependencies.
"""

import pytest
from datetime import datetime, UTC

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ContactMethod
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ClientId, TenantId, UserId, ContactInfo, Address
from app.domain.events import (
    ClientVerified,
    ClientActivated,
    ClientSuspended,
    ClientTerminated,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client_id() -> ClientId:
    return ClientId("client-123")


@pytest.fixture
def tenant_id() -> TenantId:
    return TenantId("tenant-456")


@pytest.fixture
def user_id() -> UserId:
    return UserId("user-789")


@pytest.fixture
def contact_info() -> ContactInfo:
    return ContactInfo(phone="+1-555-123-4567", email="contact@acme.com")


@pytest.fixture
def contact_info_empty() -> ContactInfo:
    return ContactInfo()


@pytest.fixture
def billing_address() -> Address:
    return Address(
        street="123 Main St",
        city="New York",
        country="USA",
        postal_code="10001",
    )


@pytest.fixture
def now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def pending_client(client_id, tenant_id, contact_info, now) -> ClientEntity:
    """Create a client in pending status."""
    return ClientEntity(
        _id=client_id,
        _tenant_id=tenant_id,
        _name="Acme Corp",
        _code="ACME",
        _contact_info=contact_info,
        _status=BaseStatus.PENDING,
        _is_verified=False,
        _created_at=now,
        _updated_at=now,
    )


@pytest.fixture
def active_client(client_id, tenant_id, contact_info, now) -> ClientEntity:
    """Create an active client."""
    return ClientEntity(
        _id=client_id,
        _tenant_id=tenant_id,
        _name="Acme Corp",
        _code="ACME",
        _contact_info=contact_info,
        _status=BaseStatus.ACTIVE,
        _is_verified=True,
        _created_at=now,
        _updated_at=now,
    )


@pytest.fixture
def deleted_client(client_id, tenant_id, contact_info, now) -> ClientEntity:
    """Create a deleted client."""
    return ClientEntity(
        _id=client_id,
        _tenant_id=tenant_id,
        _name="Deleted Corp",
        _code="DEL",
        _contact_info=contact_info,
        _status=BaseStatus.DELETED,
        _is_verified=False,
        _created_at=now,
        _updated_at=now,
        _deleted_at=now,
    )


# =============================================================================
# CREATION TESTS
# =============================================================================


class TestClientCreation:
    """Tests for client entity creation."""

    def test_create_client_success(self, client_id, tenant_id, contact_info, now):
        """Test successful client creation."""
        client = ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name="Test Corp",
            _code="TEST",
            _contact_info=contact_info,
            _status=BaseStatus.PENDING,
            _is_verified=False,
            _created_at=now,
            _updated_at=now,
        )

        assert client._id == client_id
        assert client._tenant_id == tenant_id
        assert client._name == "Test Corp"
        assert client._status == BaseStatus.PENDING
        assert client._is_verified is False


# =============================================================================
# VERIFICATION TESTS
# =============================================================================


class TestClientVerification:
    """Tests for client verification behavior."""

    def test_verify_client(self, pending_client, user_id):
        """Test verifying a client."""
        pending_client.verify(user_id)

        assert pending_client._is_verified is True
        assert any(isinstance(e, ClientVerified) for e in pending_client._events)


# =============================================================================
# ACTIVATION TESTS
# =============================================================================


class TestClientActivation:
    """Tests for client activation behavior."""

    def test_activate_pending_client(self, pending_client):
        """Test activating a pending client."""
        pending_client.activate()

        assert pending_client._status == BaseStatus.ACTIVE
        assert any(isinstance(e, ClientActivated) for e in pending_client._events)

    def test_activate_client_without_contact_raises_error(
        self, client_id, tenant_id, contact_info_empty, now
    ):
        """Test that activating client without contact info raises DomainError."""
        client = ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name="No Contact Corp",
            _code="NOC",
            _contact_info=contact_info_empty,
            _status=BaseStatus.PENDING,
            _is_verified=False,
            _created_at=now,
            _updated_at=now,
        )

        with pytest.raises(DomainError, match="Active clients must have contact info"):
            client.activate()

    def test_activate_deleted_client_raises_error(self, deleted_client):
        """Test that activating deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Cannot activate deleted client"):
            deleted_client.activate()

    def test_activate_already_active_raises_error(self, active_client):
        """Test that activating already active client raises DomainError."""
        with pytest.raises(DomainError, match="Client is already active"):
            active_client.activate()


# =============================================================================
# DEACTIVATION TESTS
# =============================================================================


class TestClientDeactivation:
    """Tests for client deactivation behavior."""

    def test_deactivate_active_client(self, active_client):
        """Test deactivating an active client."""
        active_client.deactivate()

        assert active_client._status == BaseStatus.INACTIVE

    def test_deactivate_deleted_client_raises_error(self, deleted_client):
        """Test that deactivating deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Cannot deactivate deleted client"):
            deleted_client.deactivate()

    def test_deactivate_already_inactive_raises_error(
        self, client_id, tenant_id, contact_info, now
    ):
        """Test that deactivating already inactive client raises DomainError."""
        inactive_client = ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name="Inactive Corp",
            _code="INA",
            _contact_info=contact_info,
            _status=BaseStatus.INACTIVE,
            _is_verified=False,
            _created_at=now,
            _updated_at=now,
        )

        with pytest.raises(DomainError, match="Client is already inactive"):
            inactive_client.deactivate()


# =============================================================================
# SUSPENSION TESTS
# =============================================================================


class TestClientSuspension:
    """Tests for client suspension behavior."""

    def test_suspend_active_client(self, active_client):
        """Test suspending an active client."""
        active_client.suspend("Payment overdue")

        assert active_client._status == BaseStatus.INACTIVE
        assert any(isinstance(e, ClientSuspended) for e in active_client._events)

    def test_suspend_without_reason_raises_error(self, active_client):
        """Test that suspending without reason raises DomainError."""
        with pytest.raises(DomainError, match="Suspension requires reason"):
            active_client.suspend("")

    def test_suspend_deleted_client_raises_error(self, deleted_client):
        """Test that suspending deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Cannot suspend deleted client"):
            deleted_client.suspend("Test reason")


# =============================================================================
# TERMINATION TESTS
# =============================================================================


class TestClientTermination:
    """Tests for client termination behavior."""

    def test_terminate_client(self, active_client):
        """Test terminating a client."""
        active_client.terminate("Contract ended")

        assert active_client._status == BaseStatus.DELETED
        assert active_client._deleted_at is not None
        assert any(isinstance(e, ClientTerminated) for e in active_client._events)

    def test_terminate_without_reason_raises_error(self, active_client):
        """Test that terminating without reason raises DomainError."""
        with pytest.raises(DomainError, match="Termination requires reason"):
            active_client.terminate("")

    def test_terminate_already_deleted_raises_error(self, deleted_client):
        """Test that terminating already deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Client is already terminated"):
            deleted_client.terminate("Double terminate")


# =============================================================================
# ARCHIVE TESTS
# =============================================================================


class TestClientArchive:
    """Tests for client archive behavior."""

    def test_archive_active_client(self, active_client):
        """Test archiving an active client."""
        active_client.archive()

        assert active_client._status == BaseStatus.ARCHIVED

    def test_archive_deleted_client_raises_error(self, deleted_client):
        """Test that archiving deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Cannot archive deleted client"):
            deleted_client.archive()

    def test_archive_already_archived_raises_error(
        self, client_id, tenant_id, contact_info, now
    ):
        """Test that archiving already archived client raises DomainError."""
        archived_client = ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name="Archived Corp",
            _code="ARC",
            _contact_info=contact_info,
            _status=BaseStatus.ARCHIVED,
            _is_verified=False,
            _created_at=now,
            _updated_at=now,
        )

        with pytest.raises(DomainError, match="Client is already archived"):
            archived_client.archive()


# =============================================================================
# RESTORE TESTS
# =============================================================================


class TestClientRestore:
    """Tests for client restore behavior."""

    def test_restore_archived_client(self, client_id, tenant_id, contact_info, now):
        """Test restoring an archived client."""
        archived_client = ClientEntity(
            _id=client_id,
            _tenant_id=tenant_id,
            _name="Archived Corp",
            _code="ARC",
            _contact_info=contact_info,
            _status=BaseStatus.ARCHIVED,
            _is_verified=False,
            _created_at=now,
            _updated_at=now,
        )

        archived_client.restore()

        assert archived_client._status == BaseStatus.ACTIVE

    def test_restore_deleted_client_raises_error(self, deleted_client):
        """Test that restoring deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Cannot restore deleted client"):
            deleted_client.restore()

    def test_restore_active_client_raises_error(self, active_client):
        """Test that restoring active client raises DomainError."""
        with pytest.raises(DomainError, match="Client is already active"):
            active_client.restore()


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestClientUpdate:
    """Tests for client update behavior."""

    def test_update_name(self, active_client):
        """Test updating client name."""
        active_client.update_name("New Name Corp")

        assert active_client._name == "New Name Corp"

    def test_update_name_empty_raises_error(self, active_client):
        """Test that updating with empty name raises DomainError."""
        with pytest.raises(DomainError, match="Client name cannot be empty"):
            active_client.update_name("")

    def test_update_name_deleted_client_raises_error(self, deleted_client):
        """Test that updating name for deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Cannot update name for deleted client"):
            deleted_client.update_name("New Name")

    def test_update_contact_info(self, active_client):
        """Test updating contact info."""
        new_contact = ContactInfo(phone="+1-555-999-8888")
        active_client.update_contact_info(new_contact)

        assert active_client._contact_info == new_contact

    def test_update_contact_info_deleted_raises_error(self, deleted_client):
        """Test that updating contact info for deleted client raises DomainError."""
        with pytest.raises(DomainError, match="Cannot update contact info for deleted client"):
            deleted_client.update_contact_info(ContactInfo(phone="+1-555-000-0000"))

    def test_update_billing_address(self, active_client, billing_address):
        """Test updating billing address."""
        active_client.update_billing_address(billing_address)

        assert active_client._billing_address == billing_address

    def test_update_preferred_contact_method(self, active_client):
        """Test updating preferred contact method."""
        active_client.update_preferred_contact_method(ContactMethod.EMAIL)

        assert active_client._preferred_contact_method == ContactMethod.EMAIL


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_is_active_returns_true_for_active_client(self, active_client):
        """Test is_active returns True for active client."""
        assert active_client.is_active() is True

    def test_is_active_returns_false_for_deleted_client(self, deleted_client):
        """Test is_active returns False for deleted client."""
        assert deleted_client.is_active() is False

    def test_is_active_returns_false_for_pending_client(self, pending_client):
        """Test is_active returns False for pending client."""
        assert pending_client.is_active() is False
