"""How long a booking is assumed to occupy, and what counts as a clash.

A booking records when it starts and nothing about how long it runs: `duration`
on a session is written by `complete()`, from what the counsellor reports
afterwards. Conflict detection cannot wait for that, so the length is taken
from the service being delivered, and a nominal hour stands in where the
service does not say.

That assumption is the whole basis of the clash, so it is named here rather
than buried in a query, and the API reports which length it used. See
"Decision 6" in docs/design/REALTIME_SESSION_CAPTURE.md.
"""

from datetime import datetime, timedelta

#: Used when the service carries no `duration_minutes`. An hour is the common
#: counselling appointment and errs towards catching a clash rather than
#: missing one, which is the safer direction: a false clash is questioned by a
#: person, a missed one puts a counsellor in two places at once.
DEFAULT_SESSION_MINUTES = 60


def booking_minutes(service_duration_minutes: int | None) -> int:
    """How long a booking of this service is assumed to run."""
    if service_duration_minutes is None or service_duration_minutes <= 0:
        return DEFAULT_SESSION_MINUTES
    return service_duration_minutes


def booking_end(scheduled_at: datetime, service_duration_minutes: int | None) -> datetime:
    """The instant a booking is assumed to free the practitioner again."""
    return scheduled_at + timedelta(minutes=booking_minutes(service_duration_minutes))


def spans_overlap(
    start: datetime, end: datetime, other_start: datetime, other_end: datetime
) -> bool:
    """Whether two half-open spans share any instant.

    Half-open on purpose: a booking ending at 11:00 does not clash with one
    starting at 11:00, which is the back-to-back case a scheduler relies on.
    """
    return start < other_end and other_start < end
