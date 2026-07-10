"""HMAC-SHA256 webhook signature verification (Phase 3 #D-Survey / SAD §6.4).

Provider-agnostic helper. Each ``SurveyCampaign`` carries its own per-tenant
``webhook_secret``. The ingestion endpoint computes ``HMAC-SHA256(secret, raw_body)``
and compares against the ``X-Webhook-Signature`` header in constant time.

The on-the-wire signature is hex-encoded; some providers use a ``sha256=`` prefix
(GitHub-style) so we strip it defensively.
"""

from __future__ import annotations

import hashlib
import hmac


def compute_signature(secret: str, body: bytes) -> str:
    """Return hex-encoded HMAC-SHA256 of ``body`` keyed by ``secret``."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_signature(secret: str, body: bytes, header_value: str | None) -> bool:
    """Constant-time check of an incoming webhook signature header.

    Returns False for missing / empty / malformed headers — never raises so the
    caller can return a uniform 401 without leaking which check failed.
    """
    if not header_value:
        return False
    received = header_value.strip()
    if received.lower().startswith("sha256="):
        received = received[len("sha256=") :]
    expected = compute_signature(secret, body)
    return hmac.compare_digest(expected, received)
