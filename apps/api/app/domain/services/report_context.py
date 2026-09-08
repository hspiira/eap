"""One normalized scope for every report section.

Sections used to read the run parameters individually, so a client filter or a
period could be honoured by one section and dropped by the next. The context is
built once per run, validated once, and applied by every section, and each
section echoes back the scope it applied.

The period is a pair of inclusive calendar days in ``timezone``. Timestamp
columns are filtered with ``[start_at, end_before)`` so a record on the last day
of the window is inside it; date columns use the calendar days directly.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.exceptions import DomainError

KNOWN_PARAMETERS = frozenset({"client_id", "from", "to", "timezone", "campaign_id", "status_in"})


@dataclass(frozen=True)
class ReportContext:
    """Tenant, optional client, period and timezone for one report run."""

    tenant_id: str
    client_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    timezone: str = "UTC"
    campaign_id: str | None = None
    status_in: tuple[str, ...] = ()

    def start_at(self) -> datetime | None:
        """UTC instant at which the period opens."""
        if self.date_from is None:
            return None
        return self._instant(self.date_from)

    def end_before(self) -> datetime | None:
        """UTC instant just past the period's last day; an exclusive bound."""
        if self.date_to is None:
            return None
        return self._instant(self.date_to + timedelta(days=1))

    def scope(self, *, ignored: Sequence[str] = ()) -> dict[str, Any]:
        """The scope actually applied, for the section payload and the UI."""
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "from": self.date_from.isoformat() if self.date_from else None,
            "to": self.date_to.isoformat() if self.date_to else None,
            "timezone": self.timezone,
            "campaign_id": self.campaign_id,
            "ignored_parameters": sorted(ignored),
        }

    def _instant(self, day: date) -> datetime:
        return datetime.combine(day, time.min, tzinfo=ZoneInfo(self.timezone))


def build_report_context(*, tenant_id: str, parameters: dict[str, Any]) -> ReportContext:
    """Validate run parameters and normalize them into a :class:`ReportContext`."""
    unknown = sorted(set(parameters) - KNOWN_PARAMETERS)
    if unknown:
        raise DomainError(
            f"Unsupported report parameter(s): {', '.join(unknown)}. "
            f"Supported: {', '.join(sorted(KNOWN_PARAMETERS))}"
        )
    date_from = _as_date(parameters.get("from"), field="from")
    date_to = _as_date(parameters.get("to"), field="to")
    if date_from and date_to and date_to < date_from:
        raise DomainError("Report period 'to' must be on or after 'from'")
    return ReportContext(
        tenant_id=tenant_id,
        client_id=_as_identifier(parameters.get("client_id"), field="client_id"),
        date_from=date_from,
        date_to=date_to,
        timezone=_as_timezone(parameters.get("timezone")),
        campaign_id=_as_identifier(parameters.get("campaign_id"), field="campaign_id"),
        status_in=_as_statuses(parameters.get("status_in")),
    )


def _as_date(value: Any, *, field: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise DomainError(f"Report parameter '{field}' is not a date: {value!r}") from exc
    raise DomainError(f"Report parameter '{field}' is not a date: {value!r}")


def _as_identifier(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DomainError(f"Report parameter '{field}' must be a non-empty string")
    return value


def _as_timezone(value: Any) -> str:
    if value is None:
        return "UTC"
    if not isinstance(value, str):
        raise DomainError("Report parameter 'timezone' must be an IANA timezone name")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise DomainError(f"Unknown report timezone: {value!r}") from exc
    return value


def _as_statuses(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise DomainError("Report parameter 'status_in' must be a list of statuses")
    return tuple(str(item) for item in value)
