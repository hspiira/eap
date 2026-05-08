"""Tests for the field-level envelope-encryption helpers (Phase 1 #C8)."""

import base64

import pytest

from app.core.encryption import (
    EncryptionError,
    KeyProvider,
    decrypt,
    encrypt,
    set_key_provider,
)


class _FixedKeyProvider(KeyProvider):
    def __init__(self, raw: bytes):
        self._raw = raw

    def get_kek(self) -> bytes:
        return self._raw


@pytest.fixture(autouse=True)
def isolate_provider():
    set_key_provider(_FixedKeyProvider(b"x" * 32))
    yield
    set_key_provider(_FixedKeyProvider(b"x" * 32))


class TestRoundTrip:
    def test_basic_round_trip(self):
        ct = encrypt("clinical note", tenant_id="t-1")
        assert ct is not None
        assert ct != "clinical note"
        assert decrypt(ct, tenant_id="t-1") == "clinical note"

    def test_none_passes_through(self):
        assert encrypt(None, tenant_id="t-1") is None
        assert decrypt(None, tenant_id="t-1") is None

    def test_empty_string_round_trips(self):
        ct = encrypt("", tenant_id="t-1")
        assert ct is not None
        assert decrypt(ct, tenant_id="t-1") == ""

    def test_unicode_round_trips(self):
        msg = "session summary — patient présente une anxiété généralisée"
        assert decrypt(encrypt(msg, tenant_id="t-9"), tenant_id="t-9") == msg


class TestNonDeterminism:
    def test_each_encrypt_uses_a_fresh_nonce(self):
        a = encrypt("same plaintext", tenant_id="t-1")
        b = encrypt("same plaintext", tenant_id="t-1")
        assert a != b
        assert decrypt(a, tenant_id="t-1") == decrypt(b, tenant_id="t-1") == "same plaintext"


class TestTenantIsolation:
    def test_different_tenants_produce_different_ciphertext(self):
        a = encrypt("X", tenant_id="t-1")
        b = encrypt("X", tenant_id="t-2")
        assert a != b

    def test_decrypting_with_wrong_tenant_fails(self):
        ct = encrypt("secret", tenant_id="t-1")
        with pytest.raises(EncryptionError):
            decrypt(ct, tenant_id="t-2")

    def test_empty_tenant_rejected(self):
        with pytest.raises(EncryptionError):
            encrypt("plaintext", tenant_id="")
        with pytest.raises(EncryptionError):
            decrypt("anything", tenant_id="")


class TestStorageShape:
    def test_ciphertext_is_base64(self):
        ct = encrypt("plaintext", tenant_id="t-1")
        assert ct is not None
        # Should round-trip through base64 without padding errors.
        base64.b64decode(ct, validate=True)

    def test_first_byte_is_version_marker(self):
        ct = encrypt("plaintext", tenant_id="t-1")
        assert ct is not None
        blob = base64.b64decode(ct, validate=True)
        assert blob[:1] == b"\x01"


class TestTamperDetection:
    def test_modified_ciphertext_fails_to_decrypt(self):
        ct = encrypt("payload", tenant_id="t-1")
        assert ct is not None
        blob = bytearray(base64.b64decode(ct, validate=True))
        blob[-1] ^= 0xFF
        bad = base64.b64encode(bytes(blob)).decode()
        with pytest.raises(EncryptionError):
            decrypt(bad, tenant_id="t-1")

    def test_truncated_ciphertext_rejected(self):
        with pytest.raises(EncryptionError):
            decrypt(base64.b64encode(b"\x01abc").decode(), tenant_id="t-1")


class TestKeyProvider:
    def test_changing_kek_invalidates_existing_ciphertext(self):
        ct = encrypt("payload", tenant_id="t-1")
        set_key_provider(_FixedKeyProvider(b"y" * 32))
        with pytest.raises(EncryptionError):
            decrypt(ct, tenant_id="t-1")

    def test_settings_provider_rejects_short_kek(self):
        from app.core.config import settings
        from app.core.encryption import SettingsKeyProvider

        original = settings.ENCRYPTION_KEK
        try:
            settings.ENCRYPTION_KEK = base64.b64encode(b"too-short").decode()
            with pytest.raises(EncryptionError):
                SettingsKeyProvider().get_kek()
        finally:
            settings.ENCRYPTION_KEK = original

    def test_settings_provider_rejects_non_base64(self):
        from app.core.config import settings
        from app.core.encryption import SettingsKeyProvider

        original = settings.ENCRYPTION_KEK
        try:
            settings.ENCRYPTION_KEK = "@@not-base64@@"
            with pytest.raises(EncryptionError):
                SettingsKeyProvider().get_kek()
        finally:
            settings.ENCRYPTION_KEK = original
