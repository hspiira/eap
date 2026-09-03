"""Pseudonymisation helpers.

Generates an opaque pseudonym for a ``ClinicalSubject`` that cannot be reversed
to the source ``EligibleMember`` without the audited link table. Implementation
is HMAC-SHA256 keyed by a per-tenant secret + a deterministic per-subject salt;
truncated to 16 hex chars for readability. Two members of the same tenant
cannot collide because the input includes the per-row generated cuid.
"""

from __future__ import annotations

import hashlib
import hmac

from app.shared.utils.generators import generate_cuid


def generate_pseudonym(*, tenant_secret: str, seed: str | None = None) -> str:
    if not tenant_secret or len(tenant_secret) < 16:
        raise ValueError("tenant_secret must be at least 16 characters")
    salt = seed or generate_cuid()
    digest = hmac.new(
        tenant_secret.encode("utf-8"),
        salt.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"cs_{digest[:16]}"
