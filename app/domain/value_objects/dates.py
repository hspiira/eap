from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DateRange:
    start_date: datetime
    end_date: datetime

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

    def contains(self, date: datetime) -> bool:
        return self.start_date <= date <= self.end_date

    def extend_to(self, new_end: datetime) -> "DateRange":
        return DateRange(self.start_date, new_end)
