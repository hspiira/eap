"""Diagnosis repository port (Phase 2 #D-Tax).

Read-only in v1: the taxonomy is curated centrally and seeded via migration.
"""

from abc import ABC, abstractmethod

from app.domain.entities.diagnosis import Diagnosis, DiagnosisType


class DiagnosisRepository(ABC):
    @abstractmethod
    async def list_types(self, *, active_only: bool = True) -> list[DiagnosisType]:
        ...

    @abstractmethod
    async def get_type_by_code(self, code: str) -> DiagnosisType | None:
        ...

    @abstractmethod
    async def list_diagnoses(
        self,
        *,
        type_code: str | None = None,
        active_only: bool = True,
    ) -> list[Diagnosis]:
        ...

    @abstractmethod
    async def get_diagnosis_by_code(self, code: str) -> Diagnosis | None:
        ...
