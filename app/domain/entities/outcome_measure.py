"""Outcome-measure aggregate.

Links a Case + an intake-side instrument administration + a closure-side
administration of the *same* instrument; computes the delta plus a
reliable-change-index suitable for aggregate reporting. The aggregate is the
*pairing* — neither questionnaire response is owned here, they're referenced
by id and remain on their original administering aggregate.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import TriageInstrumentCode
from app.domain.events import DomainEvent, OutcomeMeasureRecorded
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    OutcomeMeasureId,
    TenantId,
)


def reliable_change_index(
    *,
    pre_score: float,
    post_score: float,
    instrument_sd: float,
    test_retest_reliability: float,
) -> float:
    """Jacobson-Truax RCI: (post - pre) / sqrt(2 * sd^2 * (1 - r))."""
    if instrument_sd <= 0:
        raise DomainError("instrument_sd must be positive")
    if not 0 <= test_retest_reliability <= 1:
        raise DomainError("test_retest_reliability must be in [0, 1]")
    from math import sqrt

    denom = sqrt(2 * (instrument_sd ** 2) * (1 - test_retest_reliability))
    if denom == 0:
        return 0.0
    return (post_score - pre_score) / denom


@dataclass
class OutcomeMeasure:
    id: OutcomeMeasureId
    tenant_id: TenantId
    case_id: CaseId
    clinical_subject_id: ClinicalSubjectId
    instrument_code: TriageInstrumentCode
    intake_response_id: str
    closure_response_id: str
    pre_score: float
    post_score: float
    delta: float
    reliable_change_index: float
    meets_clinically_significant_change: bool
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.intake_response_id or not self.closure_response_id:
            raise DomainError(
                "OutcomeMeasure requires both intake and closure response ids"
            )
        if self.intake_response_id == self.closure_response_id:
            raise DomainError(
                "intake and closure response ids must differ"
            )
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                OutcomeMeasureRecorded(
                    occurred_at=self.created_at,
                    outcome_measure_id=self.id,
                    case_id=self.case_id,
                    instrument_code=self.instrument_code.value,
                    delta=self.delta,
                    reliable_change_index=self.reliable_change_index,
                    meets_clinically_significant_change=
                    self.meets_clinically_significant_change,
                )
            )
