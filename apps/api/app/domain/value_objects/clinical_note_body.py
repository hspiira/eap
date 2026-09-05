"""Discriminated note-body value objects (DAP, SOAP, free-form contact).

Notes are persisted as JSONB and round-tripped through ``ClinicalNote.body``.
The shape is decided by ``note_type`` and validated at construction.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import DomainError


@dataclass(frozen=True)
class DAPBody:
    data: str
    assessment: str
    plan: str

    def __post_init__(self) -> None:
        if not self.data or not self.assessment or not self.plan:
            raise DomainError("DAP note requires data, assessment, and plan")

    def as_dict(self) -> dict[str, str]:
        return {
            "data": self.data,
            "assessment": self.assessment,
            "plan": self.plan,
        }


@dataclass(frozen=True)
class SOAPBody:
    subjective: str
    objective: str
    assessment: str
    plan: str

    def __post_init__(self) -> None:
        for name, value in {
            "subjective": self.subjective,
            "objective": self.objective,
            "assessment": self.assessment,
            "plan": self.plan,
        }.items():
            if not value:
                raise DomainError(f"SOAP note requires {name}")

    def as_dict(self) -> dict[str, str]:
        return {
            "subjective": self.subjective,
            "objective": self.objective,
            "assessment": self.assessment,
            "plan": self.plan,
        }


@dataclass(frozen=True)
class NarrativeBody:
    """Free-form note body for phone / crisis contact / closure summaries."""

    summary: str

    def __post_init__(self) -> None:
        if not self.summary:
            raise DomainError("Narrative note requires a summary")

    def as_dict(self) -> dict[str, str]:
        return {"summary": self.summary}
