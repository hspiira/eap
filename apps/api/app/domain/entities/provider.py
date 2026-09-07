"""Provider aggregate.

A provider is a practitioner: the individual who delivers a session. Identity,
owned contact details and the account link live here, and so does every
lifecycle command, because panel, tier, accreditation and activation may only
change through an audited command carrying a reason.
"""

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Any

from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderGender,
    ProviderIdentityProvenance,
    ProviderTier,
    UgandaRegion,
)
from app.domain.events import DomainEvent
from app.domain.events.provider import (
    ProviderAccountLinked,
    ProviderAccountUnlinked,
    ProviderAccreditationChanged,
    ProviderCreated,
    ProviderPanelStatusChanged,
    ProviderProfileUpdated,
    ProviderStatusChanged,
    ProviderTierChanged,
)
from app.domain.exceptions import ConflictError, DomainError
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.shared.utils.datetime import utc_now


class _Unset:
    """Marks an omitted field in a partial update."""


UNSET = _Unset()

_ENTITY_FIELDS = ("display_name", "contact_email", "contact_phone", "license_info")
_PROFILE_FIELDS = ("region", "bio", "gender")


def _require_reason(reason: str) -> str:
    stripped = (reason or "").strip()
    if not stripped:
        raise DomainError("This change requires a non-blank reason")
    return stripped


def _require_display_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError("Practitioner display name is required")
    return value.strip()


def _iso(day: date | None) -> str | None:
    return day.isoformat() if day else None


@dataclass
class ProviderEntity:
    id: ProviderId
    tenant_id: TenantId
    status: BaseStatus
    display_name: str
    created_at: datetime
    updated_at: datetime
    user_id: UserId | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    identity_provenance: ProviderIdentityProvenance = ProviderIdentityProvenance.OWNED
    license_info: dict[str, object] | None = None
    provider_profile: ProviderProfile | None = None
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def _require_profile(self) -> ProviderProfile:
        self._require_not_deleted()
        if self.provider_profile is None:
            raise DomainError("Provider has no panel profile")
        return self.provider_profile

    def _require_not_deleted(self) -> None:
        if self.deleted_at is not None or self.status == BaseStatus.DELETED:
            raise DomainError("Cannot change a deleted practitioner")

    def _require_not_soft_deleted(self) -> None:
        """Weaker guard for change_status, so a record can be restored."""
        if self.deleted_at is not None:
            raise DomainError("Cannot change a deleted practitioner")

    def _touch(self) -> None:
        self.updated_at = utc_now()

    def record_created(self, actor: UserId) -> None:
        """Emit the creation event so a new practitioner reaches the audit trail."""
        self.events.append(ProviderCreated(occurred_at=utc_now(), provider_id=self.id, actor=actor))

    def apply_profile_changes(
        self,
        actor: UserId,
        *,
        display_name: str | _Unset = UNSET,
        contact_email: str | None | _Unset = UNSET,
        contact_phone: str | None | _Unset = UNSET,
        license_info: dict[str, object] | None | _Unset = UNSET,
        region: UgandaRegion | _Unset = UNSET,
        bio: str | None | _Unset = UNSET,
        gender: ProviderGender | None | _Unset = UNSET,
    ) -> tuple[str, ...]:
        """Apply a partial update to ordinary contact and profile fields.

        An omitted field stays unchanged and an explicit None clears a nullable
        field. Panel, tier, accreditation, activation and specialties are not
        reachable here; each has its own path.
        """
        requested: dict[str, Any] = {
            "display_name": display_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "license_info": license_info,
            "region": region,
            "bio": bio,
            "gender": gender,
        }
        provided = {
            name: value for name, value in requested.items() if not isinstance(value, _Unset)
        }
        self._require_not_deleted()
        changed = self._apply_entity_fields(provided) + self._apply_profile_fields(provided)
        if not changed:
            return ()
        self._touch()
        self.events.append(
            ProviderProfileUpdated(
                occurred_at=utc_now(),
                provider_id=self.id,
                changed_fields=changed,
                actor=actor,
            )
        )
        return changed

    def _apply_entity_fields(self, provided: dict[str, Any]) -> tuple[str, ...]:
        changed: list[str] = []
        for name in _ENTITY_FIELDS:
            if name not in provided:
                continue
            value = provided[name]
            if name == "display_name":
                value = _require_display_name(value)
            if getattr(self, name) == value:
                continue
            setattr(self, name, value)
            changed.append(name)
        return tuple(changed)

    def _apply_profile_fields(self, provided: dict[str, Any]) -> tuple[str, ...]:
        names = [name for name in _PROFILE_FIELDS if name in provided]
        if not names:
            return ()
        profile = self._require_profile()
        updates: dict[str, Any] = {
            name: provided[name] for name in names if getattr(profile, name) != provided[name]
        }
        if not updates:
            return ()
        self.provider_profile = replace(profile, **updates)
        return tuple(updates)

    def change_panel_status(self, new_status: PanelStatus, actor: UserId, reason: str) -> None:
        """Move the practitioner on or off the panel, emitting the audit trail."""
        checked = _require_reason(reason)
        profile = self._require_profile()
        if profile.panel_status == new_status:
            return
        self.provider_profile = replace(profile, panel_status=new_status)
        self._touch()
        self.events.append(
            ProviderPanelStatusChanged(
                occurred_at=utc_now(),
                provider_id=self.id,
                old_status=profile.panel_status.value,
                new_status=new_status.value,
                actor=actor,
                reason=checked,
            )
        )

    def change_tier(self, new_tier: ProviderTier, actor: UserId, reason: str) -> None:
        """Change the panel tier, emitting the audit trail."""
        checked = _require_reason(reason)
        profile = self._require_profile()
        if profile.tier == new_tier:
            return
        self.provider_profile = replace(profile, tier=new_tier)
        self._touch()
        self.events.append(
            ProviderTierChanged(
                occurred_at=utc_now(),
                provider_id=self.id,
                old_tier=profile.tier.value,
                new_tier=new_tier.value,
                actor=actor,
                reason=checked,
            )
        )

    def change_accreditation(
        self,
        actor: UserId,
        reason: str,
        *,
        accreditation_status: AccreditationStatus,
        accreditation_authority: str | None | _Unset = UNSET,
        accreditation_expiry: date | None | _Unset = UNSET,
    ) -> None:
        """Change accreditation status, authority and expiry as one audited command."""
        checked = _require_reason(reason)
        profile = self._require_profile()
        requested: dict[str, Any] = {
            "accreditation_status": accreditation_status,
            "accreditation_authority": accreditation_authority,
            "accreditation_expiry": accreditation_expiry,
        }
        updates = {
            name: value
            for name, value in requested.items()
            if not isinstance(value, _Unset) and getattr(profile, name) != value
        }
        if not updates:
            return
        self.provider_profile = replace(profile, **updates)
        self._touch()
        self.events.append(
            ProviderAccreditationChanged(
                occurred_at=utc_now(),
                provider_id=self.id,
                old_status=profile.accreditation_status.value,
                new_status=self.provider_profile.accreditation_status.value,
                old_expiry=_iso(profile.accreditation_expiry),
                new_expiry=_iso(self.provider_profile.accreditation_expiry),
                actor=actor,
                reason=checked,
            )
        )

    def change_status(self, new_status: BaseStatus, actor: UserId, reason: str) -> None:
        """Activate or deactivate the practitioner record."""
        checked = _require_reason(reason)
        self._require_not_soft_deleted()
        if self.status == new_status:
            return
        previous = self.status
        self.status = new_status
        self._touch()
        self.events.append(
            ProviderStatusChanged(
                occurred_at=utc_now(),
                provider_id=self.id,
                old_status=previous.value,
                new_status=new_status.value,
                actor=actor,
                reason=checked,
            )
        )

    def link_account(self, user_id: UserId, actor: UserId, reason: str) -> None:
        """Link a user account. Linking grants no role and copies no contact data."""
        checked = _require_reason(reason)
        self._require_not_deleted()
        if self.user_id == user_id:
            return
        if self.user_id is not None:
            raise ConflictError(
                "Practitioner already has a linked account; unlink it first",
                details={"provider_id": self.id.value, "user_id": self.user_id.value},
            )
        self.user_id = user_id
        self._touch()
        self.events.append(
            ProviderAccountLinked(
                occurred_at=utc_now(),
                provider_id=self.id,
                user_id=user_id,
                actor=actor,
                reason=checked,
            )
        )

    def unlink_account(self, actor: UserId, reason: str) -> None:
        """Remove the account link. The practitioner and their sessions remain."""
        checked = _require_reason(reason)
        if self.user_id is None:
            return
        previous = self.user_id
        self.user_id = None
        self._touch()
        self.events.append(
            ProviderAccountUnlinked(
                occurred_at=utc_now(),
                provider_id=self.id,
                user_id=previous,
                actor=actor,
                reason=checked,
            )
        )

    def clear_events(self) -> None:
        self.events.clear()
