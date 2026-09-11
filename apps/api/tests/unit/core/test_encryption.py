"""Tests for the field-level envelope-encryption helpers (Phase 1 #C8)."""

import base64

import pytest

from app.core.encryption import (
    AWSKMSKeyProvider,
    EncryptionError,
    KeyProvider,
    SettingsKeyProvider,
    decrypt,
    encrypt,
    get_key_provider,
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
        msg = "session summary, patient présente une anxiété généralisée"
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


class _FakeKMSClient:
    """Stands in for a boto3 KMS client: decrypts whatever it last "generated"."""

    def __init__(self, plaintext_kek: bytes):
        self._plaintext_kek = plaintext_kek
        self.decrypt_calls = 0

    def decrypt(self, *, CiphertextBlob: bytes, KeyId: str):  # noqa: N803 (matches boto3's shape)
        self.decrypt_calls += 1
        if CiphertextBlob != b"wrapped:" + self._plaintext_kek:
            raise ValueError("wrong ciphertext for this key")
        return {"Plaintext": self._plaintext_kek}


class TestAWSKMSKeyProvider:
    def _provider(
        self, plaintext_kek=b"k" * 32, **kwargs
    ) -> tuple[AWSKMSKeyProvider, _FakeKMSClient]:
        client = _FakeKMSClient(plaintext_kek)
        ciphertext_b64 = base64.b64encode(b"wrapped:" + plaintext_kek).decode()
        return AWSKMSKeyProvider(client, "key-1", ciphertext_b64, **kwargs), client

    def test_get_kek_returns_the_kms_decrypted_plaintext(self):
        provider, _client = self._provider(b"k" * 32)
        assert provider.get_kek() == b"k" * 32

    def test_a_short_kms_decrypted_key_is_rejected(self):
        provider, _client = self._provider(b"short")
        with pytest.raises(EncryptionError):
            provider.get_kek()

    def test_invalid_base64_ciphertext_is_rejected_at_construction(self):
        with pytest.raises(EncryptionError):
            AWSKMSKeyProvider(_FakeKMSClient(b"k" * 32), "key-1", "@@not-base64@@")

    def test_a_kms_decrypt_failure_becomes_an_encryption_error(self):
        provider, client = self._provider()
        client.decrypt = lambda **_: (_ for _ in ()).throw(RuntimeError("access denied"))
        with pytest.raises(EncryptionError):
            provider.get_kek()

    def test_repeated_calls_within_the_cache_window_do_not_call_kms_again(self):
        """encrypt/decrypt call get_kek on every field, so an uncached provider would hit KMS per field."""
        provider, client = self._provider(cache_ttl_seconds=300.0)
        for _ in range(5):
            provider.get_kek()
        assert client.decrypt_calls == 1

    def test_the_cache_expires_after_its_ttl(self, monkeypatch):
        import time as time_module

        real_monotonic = time_module.monotonic
        provider, client = self._provider(cache_ttl_seconds=1.0)
        provider.get_kek()
        monkeypatch.setattr(time_module, "monotonic", lambda: real_monotonic() + 2.0)
        provider.get_kek()
        assert client.decrypt_calls == 2


class TestGetKeyProvider:
    def test_defaults_to_the_settings_provider(self):
        assert isinstance(get_key_provider(), SettingsKeyProvider)

    def test_unrecognised_provider_type_falls_back_to_settings(self):
        assert isinstance(get_key_provider("something-else"), SettingsKeyProvider)

    def test_aws_kms_with_no_key_id_falls_back_to_settings(self):
        """Matches get_login_rate_limit_backend: an unconfigured real backend never blocks startup."""
        assert isinstance(
            get_key_provider("aws-kms", kms_key_id="", kek_ciphertext="anything"),
            SettingsKeyProvider,
        )

    def test_aws_kms_with_boto3_unavailable_falls_back_to_settings(self):
        """boto3 is an optional dependency (the `kms` extra); this environment does not install it."""
        provider = get_key_provider("aws-kms", kms_key_id="key-1", kek_ciphertext="Y2lwaGVy")
        assert isinstance(provider, SettingsKeyProvider)
