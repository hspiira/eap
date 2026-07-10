"""DSAR collection + tombstoning protocols (Phase 4 #DSAR / SAD §6.6).

Cross-aggregate orchestration belongs to the application layer, but the
heavy-lifting SQL queries (collect everything tied to a subject) live in
infrastructure. The protocols below let use cases stay test-friendly while
infra implementations get free rein over join strategy.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.value_objects.core import PersonId, TenantId


class DSARDataCollector(Protocol):
    """Walks every aggregate that may hold data tied to ``subject_person_id``.

    Returns a JSON-serialisable bundle. The bundle is opaque — its shape is
    decided by the implementation and consumed by the export route, not by
    business logic in the use case.
    """

    async def collect(
        self,
        *,
        tenant_id: TenantId,
        subject_person_id: PersonId,
    ) -> dict[str, Any]:
        ...


class DSARTombstoner(Protocol):
    """Overwrites PII fields with synthetic placeholders, preserving row identity.

    Returning the tombstone token (an opaque per-subject hash) lets the audit
    chain link future references to the now-erased subject without leaking PII.
    """

    async def tombstone(
        self,
        *,
        tenant_id: TenantId,
        subject_person_id: PersonId,
    ) -> str:
        ...
