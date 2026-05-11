"""Per-EAP-programme session-cap rules.

A ``ProgrammeSessionCap`` describes how many sessions of a given service
category an eligible member may consume per issue, per year, and per
household per year. The numbers come from the corporate contract; the
``Authorization`` aggregate instantiates a per-Case ledger from these caps.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import ServiceCategory
from app.domain.exceptions import DomainError


@dataclass(frozen=True)
class ProgrammeSessionCap:
    service_category: ServiceCategory
    per_issue_per_year: int
    per_year: int | None = None
    per_household_per_year: int | None = None

    def __post_init__(self) -> None:
        if self.per_issue_per_year < 0:
            raise DomainError("per_issue_per_year cannot be negative")
        if self.per_year is not None and self.per_year < self.per_issue_per_year:
            raise DomainError(
                "per_year cannot be less than per_issue_per_year"
            )
        if (
            self.per_household_per_year is not None
            and self.per_year is not None
            and self.per_household_per_year < self.per_year
        ):
            raise DomainError(
                "per_household_per_year cannot be less than per_year"
            )

    def as_dict(self) -> dict[str, int | str | None]:
        return {
            "service_category": self.service_category.value,
            "per_issue_per_year": self.per_issue_per_year,
            "per_year": self.per_year,
            "per_household_per_year": self.per_household_per_year,
        }
