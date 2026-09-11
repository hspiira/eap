"""Field-level envelope encryption for clinical PII (Phase 1 #C8).

The platform uses AES-256-GCM for authenticated encryption. A per-tenant
data-encryption key (DEK) is HKDF-derived from a single key-encryption key
(KEK), so two tenants encrypting the same plaintext produce different
ciphertexts and decryption always requires the tenant context.

The KEK is sourced via :class:`KeyProvider`. :func:`get_key_provider` builds
the right one from config (``ENCRYPTION_KEY_PROVIDER``): ``"settings"`` reads
``settings.ENCRYPTION_KEK`` directly (dev/test only), ``"aws-kms"`` envelope-
decrypts it from AWS KMS via :class:`AWSKMSKeyProvider`. The app lifespan
calls :func:`set_key_provider` once at startup with the result.

Ciphertext on disk is a base64 string with the layout::

    b64(version || nonce || aes_gcm_tag || ciphertext)

The version byte gives a forward-compatible upgrade path for KEK rotation
or algorithm change without re-encrypting the whole table at once.
"""

from __future__ import annotations

import base64
import os
import time
from abc import ABC, abstractmethod
from functools import lru_cache
from threading import RLock
from typing import overload

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import settings

_VERSION_V1 = b"\x01"
_NONCE_BYTES = 12
_DEK_BYTES = 32
_KEK_MIN_BYTES = 32


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class KeyProvider(ABC):
    """Abstraction over the key-encryption-key source."""

    @abstractmethod
    def get_kek(self) -> bytes:
        """Return raw KEK bytes (>= 32 bytes)."""


class SettingsKeyProvider(KeyProvider):
    """Reads the KEK from ``settings.ENCRYPTION_KEK`` (base64 of >=32 bytes).

    For development, an empty value falls back to a deterministic, repo-wide
    test key so tests and dev databases work without ceremony. Production
    must set ``ENCRYPTION_KEK`` to a real value (or supply a different
    :class:`KeyProvider`).
    """

    _DEV_FALLBACK = base64.b64encode(b"evexia-dev-only-do-not-use-prod!").decode()

    def get_kek(self) -> bytes:
        configured = (settings.ENCRYPTION_KEK or "").strip()
        encoded = configured or self._DEV_FALLBACK
        try:
            raw = base64.b64decode(encoded, validate=True)
        except Exception as exc:
            raise EncryptionError("ENCRYPTION_KEK is not valid base64") from exc
        if len(raw) < _KEK_MIN_BYTES:
            raise EncryptionError(
                f"ENCRYPTION_KEK must be >= {_KEK_MIN_BYTES} bytes (got {len(raw)})"
            )
        return raw


class AWSKMSKeyProvider(KeyProvider):
    """Envelope-decrypts the KEK from AWS KMS, cached in-process.

    The KEK never sits in application config as plaintext. A one-time
    bootstrap (``scripts/generate_kms_kek.py``) asks KMS to mint a data key
    and this process only ever holds its KMS-encrypted ciphertext blob
    (``ENCRYPTION_KEK_CIPHERTEXT``). ``get_kek`` calls KMS ``Decrypt`` to
    recover the plaintext bytes and caches them for ``cache_ttl_seconds``,
    matching this codebase's existing in-process caching convention (see the
    platform vocabulary cache): every ``encrypt``/``decrypt`` call reads
    ``get_kek()`` (see ``_dek_for``), so an uncached provider would call KMS
    on every single field access.
    """

    def __init__(
        self,
        client,
        key_id: str,
        kek_ciphertext_b64: str,
        *,
        cache_ttl_seconds: float = 300.0,
    ) -> None:
        self._client = client
        self._key_id = key_id
        try:
            self._ciphertext = base64.b64decode(kek_ciphertext_b64, validate=True)
        except Exception as exc:
            raise EncryptionError("ENCRYPTION_KEK_CIPHERTEXT is not valid base64") from exc
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cached_kek: bytes | None = None
        self._cached_at: float = 0.0
        self._lock = RLock()

    def get_kek(self) -> bytes:
        with self._lock:
            now = time.monotonic()
            if self._cached_kek is not None and (now - self._cached_at) < self._cache_ttl_seconds:
                return self._cached_kek
            try:
                response = self._client.decrypt(CiphertextBlob=self._ciphertext, KeyId=self._key_id)
            except Exception as exc:
                raise EncryptionError("AWS KMS decrypt failed") from exc
            kek = response["Plaintext"]
            if len(kek) < _KEK_MIN_BYTES:
                raise EncryptionError(
                    f"KMS-decrypted KEK must be >= {_KEK_MIN_BYTES} bytes (got {len(kek)})"
                )
            self._cached_kek = kek
            self._cached_at = now
            return kek


def _aws_kms_provider(kms_key_id: str, kek_ciphertext: str) -> KeyProvider | None:
    """Build the AWS KMS provider if boto3 is installed and config is present."""
    if not kms_key_id or not kek_ciphertext:
        return None
    try:
        import boto3
    except ImportError:
        return None
    return AWSKMSKeyProvider(boto3.client("kms"), kms_key_id, kek_ciphertext)


def get_key_provider(
    provider_type: str = "settings",
    *,
    kms_key_id: str = "",
    kek_ciphertext: str = "",
) -> KeyProvider:
    """Build the KeyProvider for the given config.

    Mirrors ``get_login_rate_limit_backend``'s pluggable-backend shape: an
    unavailable or unconfigured real backend falls back to the always-usable
    default rather than failing startup, and a caller who needs to know
    which one it actually got reads the returned instance's type.
    """
    if provider_type == "aws-kms":
        kms_provider = _aws_kms_provider(kms_key_id, kek_ciphertext)
        if kms_provider is not None:
            return kms_provider
    return SettingsKeyProvider()


_provider: KeyProvider = SettingsKeyProvider()
_provider_lock = RLock()


def set_key_provider(provider: KeyProvider) -> None:
    """Replace the active KeyProvider. Call at startup before any encryption."""
    global _provider
    with _provider_lock:
        _provider = provider
        _derive_dek.cache_clear()


@lru_cache(maxsize=256)
def _derive_dek(tenant_id: str, kek_fingerprint: bytes) -> bytes:
    kek = _provider.get_kek()
    if hashes_fingerprint(kek) != kek_fingerprint:
        raise EncryptionError("KEK fingerprint mismatch (provider replaced?)")
    return HKDF(
        algorithm=hashes.SHA256(),
        length=_DEK_BYTES,
        salt=b"evexia.tenant." + tenant_id.encode(),
        info=b"evexia.dek.v1",
    ).derive(kek)


def hashes_fingerprint(kek: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(kek)
    return digest.finalize()[:8]


def _dek_for(tenant_id: str) -> bytes:
    if not tenant_id:
        raise EncryptionError("tenant_id is required for encryption")
    fp = hashes_fingerprint(_provider.get_kek())
    return _derive_dek(tenant_id, fp)


@overload
def encrypt(plaintext: str, tenant_id: str) -> str: ...
@overload
def encrypt(plaintext: None, tenant_id: str) -> None: ...
def encrypt(plaintext: str | None, tenant_id: str) -> str | None:
    """Encrypt ``plaintext`` under the per-tenant DEK; return base64 ciphertext."""
    if plaintext is None:
        return None
    aes = AESGCM(_dek_for(tenant_id))
    nonce = os.urandom(_NONCE_BYTES)
    body = aes.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return base64.b64encode(_VERSION_V1 + nonce + body).decode("ascii")


@overload
def decrypt(ciphertext: str, tenant_id: str) -> str: ...
@overload
def decrypt(ciphertext: None, tenant_id: str) -> None: ...
def decrypt(ciphertext: str | None, tenant_id: str) -> str | None:
    """Decrypt ``ciphertext`` produced by :func:`encrypt` for the same tenant."""
    if ciphertext is None:
        return None
    try:
        blob = base64.b64decode(ciphertext, validate=True)
    except Exception as exc:
        raise EncryptionError("ciphertext is not valid base64") from exc
    if len(blob) < 1 + _NONCE_BYTES + 16:
        raise EncryptionError("ciphertext too short")
    version, rest = blob[:1], blob[1:]
    if version != _VERSION_V1:
        raise EncryptionError(f"unsupported ciphertext version: {version!r}")
    nonce, body = rest[:_NONCE_BYTES], rest[_NONCE_BYTES:]
    aes = AESGCM(_dek_for(tenant_id))
    try:
        return aes.decrypt(nonce, body, associated_data=None).decode("utf-8")
    except Exception as exc:
        raise EncryptionError("decryption failed (wrong tenant or tampered data)") from exc
