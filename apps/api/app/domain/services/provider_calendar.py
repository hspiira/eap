"""The tenant calendar every date-valued provider boundary resolves against.

Accreditation expiry and affiliation validity are both date-valued business
boundaries, so both must resolve their day in the same zone. Decision 7 adopts
Africa/Kampala for this release until a tenant timezone column exists; when one
lands, this module is the only place that changes.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

PROVIDER_BOUNDARY_TIMEZONE = ZoneInfo("Africa/Kampala")


def boundary_day(moment: datetime) -> date:
    """The calendar day a moment falls on in the provider boundary timezone.

    Rejects a naive datetime rather than assuming the server's zone.
    """
    if moment.tzinfo is None:
        raise ValueError("A provider boundary needs an aware datetime, not a naive one")
    return moment.astimezone(PROVIDER_BOUNDARY_TIMEZONE).date()
