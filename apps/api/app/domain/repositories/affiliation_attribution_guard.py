"""The seam agent 1's attribution check plugs into.

Narrowing an affiliation's interval can stop it covering a session that is
already completed and attributed to it. Decision 2 forbids doing that silently.
The check reads session attribution, which agent 1 owns, but the only interval
mutation lives here, so the port is declared on this side and implemented on
theirs.
"""

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import ProviderAffiliationId


class AffiliationAttributionGuard(Protocol):
    async def sessions_orphaned_by(
        self,
        tenant_id: TenantId,
        affiliation_id: ProviderAffiliationId,
        *,
        new_valid_until: date | None,
    ) -> Sequence[str]:
        """Ids of completed sessions the narrowed interval would stop covering.

        Empty when the change is safe. Widening an interval never orphans
        anything, so an implementation may return empty without querying.
        """
        ...
