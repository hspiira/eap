"""Reads the display names a session list renders next to its identifiers.

A separate port from the entity repositories because it answers one question,
in bulk, for list responses. The list endpoint returned bare ids, so the UI
issued one member fetch per row: a 20-row page cost 20 extra requests, and a
company-wide session, which has no member, could not name its client at all.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.domain.value_objects.core import TenantId


@dataclass(frozen=True)
class SessionNames:
    """Display names keyed by id. Unresolved ids are absent, never None."""

    clients: dict[str, str] = field(default_factory=dict[str, str])
    members: dict[str, str] = field(default_factory=dict[str, str])
    providers: dict[str, str] = field(default_factory=dict[str, str])
    services: dict[str, str] = field(default_factory=dict[str, str])


class SessionNameReader(ABC):
    @abstractmethod
    async def names_for(
        self,
        tenant_id: TenantId,
        *,
        client_ids: Sequence[str],
        member_ids: Sequence[str],
        provider_ids: Sequence[str],
        service_ids: Sequence[str],
    ) -> SessionNames:
        """Resolve names for one page of sessions, one query per entity kind."""
