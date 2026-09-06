"""The timezone a date-valued provider boundary is evaluated in.

Decision 7 adopts the configured tenant timezone with Africa/Kampala as this
release's default, for accreditation expiry. An affiliation interval is the
same kind of boundary, so agent 1 and agent 2 agreed to evaluate both here.
Evaluating one in Kampala and the other in UTC would put a session scheduled
just after midnight on different days in two halves of one eligibility answer.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

PROVIDER_BOUNDARY_TIMEZONE = ZoneInfo("Africa/Kampala")


def boundary_day(moment: datetime) -> date:
    """The business day a moment falls on, for interval and expiry comparisons."""
    if moment.tzinfo is None:
        raise ValueError("A provider boundary needs a timezone-aware datetime")
    return moment.astimezone(PROVIDER_BOUNDARY_TIMEZONE).date()
