"""The timezone every date-valued provider boundary is evaluated in.

Decision 7 adopts the configured tenant timezone with Africa/Kampala as this
release's default, for accreditation expiry. An affiliation interval and a
completed session's attribution are the same kind of boundary, so all of them
resolve their day here. Evaluating one in Kampala and another in UTC would put
a session scheduled just after midnight on different days in two halves of one
answer. When a tenant timezone column lands, this constant is the only thing
that changes.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

PROVIDER_BOUNDARY_TIMEZONE = ZoneInfo("Africa/Kampala")


def boundary_day(moment: datetime) -> date:
    """The business day a moment falls on, for interval and expiry comparisons."""
    if moment.tzinfo is None:
        raise ValueError("A provider boundary needs a timezone-aware datetime")
    return moment.astimezone(PROVIDER_BOUNDARY_TIMEZONE).date()
