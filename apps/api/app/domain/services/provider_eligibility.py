"""Booking eligibility for a practitioner.

One rule set, used by the eligibility preview endpoint and by every write path
that books or assigns work. Present-day restrictions govern new work; nothing
here is consulted when accepting a historical record.

Pure functions; no IO. Organisation approval and affiliation validity extend
this in phase 3 through ``extend`` rather than a second rule set. Date-valued
boundaries resolve their day through ``provider_calendar.boundary_day``.
"""

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.entities.provider import ProviderEntity
from app.domain.enums import AccreditationStatus, BaseStatus, PanelStatus
from app.domain.exceptions import DomainError
from app.domain.services.provider_calendar import boundary_day


@dataclass(frozen=True)
class EligibilityReason:
    code: str
    message: str


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    reasons: tuple[EligibilityReason, ...]

    @classmethod
    def from_reasons(cls, reasons: tuple[EligibilityReason, ...]) -> "EligibilityDecision":
        return cls(eligible=not reasons, reasons=reasons)

    def extend(self, more: tuple[EligibilityReason, ...]) -> "EligibilityDecision":
        return EligibilityDecision.from_reasons(self.reasons + more)


class ProviderNotEligibleError(DomainError):
    """A write path refused a booking or assignment on eligibility grounds."""

    def __init__(self, provider_id: str, reasons: tuple[EligibilityReason, ...]):
        self.provider_id = provider_id
        self.reasons = reasons
        super().__init__(
            "Provider is not eligible for this booking",
            error_code="PROVIDER_NOT_ELIGIBLE",
            http_status=409,
        )

    def to_api_response(self, path: str | None = None, request_id: str | None = None):
        body = super().to_api_response(path, request_id)
        body["details"] = [
            {"field": "provider_id", "message": self.provider_id, "code": "provider_id"},
            *(
                {"field": "eligibility", "message": reason.message, "code": reason.code}
                for reason in self.reasons
            ),
        ]
        return body


def evaluate_practitioner(
    provider: ProviderEntity, *, scheduled_at: datetime, now: datetime
) -> EligibilityDecision:
    """Whether this practitioner may take new work scheduled at ``scheduled_at``.

    A deleted record reports only that. Otherwise every failing rule is
    reported, so a caller can show all of them rather than the first.
    """
    if provider.deleted_at is not None:
        return EligibilityDecision.from_reasons(
            (EligibilityReason("provider_deleted", "Practitioner record has been deleted"),)
        )
    return EligibilityDecision.from_reasons(
        _status_reasons(provider) + _profile_reasons(provider, scheduled_at, now)
    )


def _status_reasons(provider: ProviderEntity) -> tuple[EligibilityReason, ...]:
    if provider.status == BaseStatus.ACTIVE:
        return ()
    return (
        EligibilityReason(
            "provider_not_active",
            f"Practitioner record status is {provider.status.value}, not Active",
        ),
    )


def _profile_reasons(
    provider: ProviderEntity, scheduled_at: datetime, now: datetime
) -> tuple[EligibilityReason, ...]:
    profile = provider.provider_profile
    if profile is None:
        return (EligibilityReason("provider_no_profile", "Practitioner has no panel profile"),)
    reasons: list[EligibilityReason] = []
    if profile.panel_status != PanelStatus.ACTIVE:
        reasons.append(
            EligibilityReason(
                "panel_not_active", f"Panel status is {profile.panel_status.value}, not Active"
            )
        )
    if profile.accreditation_status != AccreditationStatus.ACCREDITED:
        reasons.append(
            EligibilityReason(
                "not_accredited",
                f"Accreditation status is {profile.accreditation_status.value}, not Accredited",
            )
        )
    expired = _expiry_reason(profile.accreditation_expiry, scheduled_at, now)
    if expired is not None:
        reasons.append(expired)
    return tuple(reasons)


def _expiry_reason(
    expiry: date | None, scheduled_at: datetime, now: datetime
) -> EligibilityReason | None:
    """An expiry date is valid through that day, for both today and the service date."""
    if expiry is None:
        return None
    today = boundary_day(now)
    service_day = boundary_day(scheduled_at)
    if expiry >= today and expiry >= service_day:
        return None
    message = (
        f"Accreditation expired on {expiry.isoformat()}. It must cover both "
        f"{today.isoformat()} and the service date {service_day.isoformat()}"
    )
    return EligibilityReason("accreditation_expired", message)


def require_eligible(decision: EligibilityDecision, provider_id: str) -> None:
    """Raise the 409 when a write path is not permitted to proceed."""
    if not decision.eligible:
        raise ProviderNotEligibleError(provider_id, decision.reasons)
