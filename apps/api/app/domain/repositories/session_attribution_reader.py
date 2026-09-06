"""Reads the organisation a session was delivered through.

The organisation is resolved from the affiliation stored on the session, never
from the practitioner's current affiliations, so a practitioner changing firms
does not reattribute delivery that already happened.

A separate port from the affiliation repository because it answers a question
about sessions, in bulk, for list responses that would otherwise issue one
lookup per row.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.value_objects.core import TenantId


class SessionAttributionReader(ABC):
    @abstractmethod
    async def organisation_ids_by_affiliation(
        self, tenant_id: TenantId, affiliation_ids: Sequence[str]
    ) -> dict[str, str]:
        """Map each affiliation id to the organisation it belongs to.

        Ids that do not resolve within the tenant are absent from the result
        rather than mapped to None, so a caller cannot mistake an unresolved
        reference for a session with no organisation.
        """
