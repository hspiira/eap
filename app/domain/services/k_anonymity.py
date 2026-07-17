"""K-anonymity gate for cross-tenant benchmark queries (Phase 4 #D-Benchmark).

Per assumption A-19, no aggregate that contains fewer than ``K_FLOOR``
contributing tenants is ever surfaced. The enforcement is pure: pass in a
contributor count + an aggregate value, get back either the value (if
disclosure is permitted) or a structured suppression result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

K_ANON_FLOOR = 10
"""Minimum distinct contributing tenants required to surface an aggregate.

Sourced from SAD A-19. Override only at test-fixture level — tightening (raising
the floor) is always safe; loosening requires legal sign-off and a new ADR.
"""


@dataclass(frozen=True)
class BenchmarkResult:
    """Wrapper around an aggregate value that may have been suppressed."""

    metric_code: str
    contributor_count: int
    floor: int
    suppressed: bool
    suppression_reason: str | None
    value: Any | None

    def is_disclosed(self) -> bool:
        return not self.suppressed


def enforce_k_anonymity(
    *,
    metric_code: str,
    contributor_count: int,
    value: Any,
    floor: int = K_ANON_FLOOR,
) -> BenchmarkResult:
    """Return the value if k ≥ floor; otherwise a suppressed result.

    Suppression returns a result rather than raising so callers can compose
    multi-metric responses without fragile try/except per metric.
    """
    if contributor_count < floor:
        return BenchmarkResult(
            metric_code=metric_code,
            contributor_count=contributor_count,
            floor=floor,
            suppressed=True,
            suppression_reason=(
                f"k-anonymity floor not met: {contributor_count} contributor(s) "
                f"< {floor} required"
            ),
            value=None,
        )
    return BenchmarkResult(
        metric_code=metric_code,
        contributor_count=contributor_count,
        floor=floor,
        suppressed=False,
        suppression_reason=None,
        value=value,
    )
