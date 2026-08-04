"""Cell-suppression for employer-facing aggregate reports.

Mirror of the cross-tenant k-anonymity gate, scoped to a *single* tenant: any
bucket whose count falls below ``MinimumCellSize`` is replaced with the
sentinel string ``"<{floor}"`` so a small employer querying e.g.
"diagnoses by month" cannot re-identify an individual.

Pure functions; no IO. Wire from the route layer immediately before
serialisation so business logic stays oblivious to disclosure rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_MIN_CELL_SIZE = 5


@dataclass(frozen=True)
class MinimumCellSize:
    """Per-tenant disclosure floor for employer-facing aggregates."""

    floor: int = DEFAULT_MIN_CELL_SIZE

    def __post_init__(self) -> None:
        if self.floor < 1:
            raise ValueError("MinimumCellSize.floor must be >= 1")


def _suppression_token(floor: int) -> str:
    return f"<{floor}"


def suppress_count(value: int, *, floor: int = DEFAULT_MIN_CELL_SIZE) -> int | str:
    """Return the value when ``value >= floor``; otherwise the suppression token."""
    return value if value >= floor else _suppression_token(floor)


def suppress_count_dict(
    counts: dict[str, int], *, floor: int = DEFAULT_MIN_CELL_SIZE
) -> dict[str, int | str]:
    """Apply suppression to every value of a flat ``label -> count`` dict."""
    return {key: suppress_count(value, floor=floor) for key, value in counts.items()}


def suppress_bucket_list(
    buckets: list[dict[str, Any]],
    *,
    count_field: str = "count",
    floor: int = DEFAULT_MIN_CELL_SIZE,
    drop_below_floor: bool = False,
) -> list[dict[str, Any]]:
    """Apply suppression to a list-of-records aggregate.

    When ``drop_below_floor`` is True, sub-floor rows are removed entirely (use
    for time-series where a placeholder row would be misleading); otherwise
    the count is replaced with the suppression token while the label is kept.
    """
    out: list[dict[str, Any]] = []
    for row in buckets:
        raw = row.get(count_field, 0)
        if not isinstance(raw, int):
            out.append(row)
            continue
        if raw < floor:
            if drop_below_floor:
                continue
            new_row = dict(row)
            new_row[count_field] = _suppression_token(floor)
            out.append(new_row)
        else:
            out.append(row)
    return out


def is_suppressed(value: int | str) -> bool:
    return isinstance(value, str) and value.startswith("<")
