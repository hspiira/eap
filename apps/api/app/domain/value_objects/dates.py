from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DateRange:
    """An inclusive span of calendar days.

    Contract terms are agreed as days rather than instants, so both bounds are dates.
    """

    start_date: date
    end_date: date

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days

    @property
    def months(self) -> int:
        return (self.end_date.year - self.start_date.year) * 12 + (
            self.end_date.month - self.start_date.month
        )

    @property
    def years(self) -> int:
        return self.end_date.year - self.start_date.year

    def contains(self, day: date) -> bool:
        return self.start_date <= day <= self.end_date

    def extend_to(self, new_end: date) -> "DateRange":
        return DateRange(self.start_date, new_end)
