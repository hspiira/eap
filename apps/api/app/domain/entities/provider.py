"""Provider aggregate."""

from dataclasses import dataclass, field, replace
from datetime import datetime

from app.domain.enums import BaseStatus, PanelStatus, ProviderTier
from app.domain.events import DomainEvent
from app.domain.events.provider import ProviderPanelStatusChanged, ProviderTierChanged
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.shared.utils.datetime import utc_now


@dataclass
class ProviderEntity:
    id: ProviderId
    tenant_id: TenantId
    user_id: UserId
    status: BaseStatus
    created_at: datetime
    updated_at: datetime
    license_info: dict[str, object] | None = None
    provider_profile: ProviderProfile | None = None
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def replace_profile(self, profile: ProviderProfile) -> None:
        self.provider_profile = profile

    def _require_profile(self) -> ProviderProfile:
        if self.provider_profile is None:
            raise DomainError("Provider has no panel profile")
        return self.provider_profile

    def change_panel_status(self, new_status: PanelStatus, actor: UserId, reason: str) -> None:
        """Move the provider on or off the panel, emitting the audit trail."""
        profile = self._require_profile()
        if profile.panel_status == new_status:
            return
        self.provider_profile = replace(profile, panel_status=new_status)
        self.events.append(
            ProviderPanelStatusChanged(
                occurred_at=utc_now(),
                provider_id=self.id,
                old_status=profile.panel_status.value,
                new_status=new_status.value,
                actor=actor,
                reason=reason,
            )
        )

    def change_tier(self, new_tier: ProviderTier, actor: UserId, reason: str) -> None:
        """Change the panel tier, emitting the audit trail."""
        profile = self._require_profile()
        self.provider_profile = replace(profile, tier=new_tier)
        self.events.append(
            ProviderTierChanged(
                occurred_at=utc_now(),
                provider_id=self.id,
                old_tier=profile.tier.value,
                new_tier=new_tier.value,
                actor=actor,
                reason=reason,
            )
        )

    def clear_events(self) -> None:
        self.events.clear()
