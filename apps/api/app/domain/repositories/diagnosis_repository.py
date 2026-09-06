"""Diagnosis repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
Per-tenant preference lives in the overlay methods at the bottom, which never
change the shared rows.
"""

from abc import ABC, abstractmethod

from app.domain.entities.diagnosis import (
    Diagnosis,
    DiagnosisAlias,
    DiagnosisType,
    TenantOverlay,
)


class DiagnosisRepository(ABC):
    @abstractmethod
    async def list_types(self, *, active_only: bool = True) -> list[DiagnosisType]: ...

    @abstractmethod
    async def get_type_by_code(self, code: str) -> DiagnosisType | None: ...

    @abstractmethod
    async def list_diagnoses(
        self,
        *,
        type_code: str | None = None,
        active_only: bool = True,
    ) -> list[Diagnosis]: ...

    @abstractmethod
    async def get_diagnosis_by_code(self, code: str) -> Diagnosis | None: ...

    # === Writes (platform admin only) ===

    @abstractmethod
    async def create_type(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> DiagnosisType: ...

    @abstractmethod
    async def update_type(
        self,
        type_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> DiagnosisType | None: ...

    @abstractmethod
    async def set_type_active(self, type_id: str, *, is_active: bool) -> DiagnosisType | None: ...

    @abstractmethod
    async def create_diagnosis(
        self, *, type_id: str, code: str, name: str, description: str | None, sort_order: int
    ) -> Diagnosis: ...

    @abstractmethod
    async def update_diagnosis(
        self,
        diagnosis_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> Diagnosis | None: ...

    @abstractmethod
    async def set_diagnosis_active(
        self, diagnosis_id: str, *, is_active: bool
    ) -> Diagnosis | None: ...

    # === Tenant overlay ===

    @abstractmethod
    async def tenant_overlay(self, tenant_id: str) -> dict[tuple[str, str | None], TenantOverlay]:
        """Overlay rows for a tenant, keyed by (diagnosis_type_id, diagnosis_id)."""

    @abstractmethod
    async def set_tenant_overlay(
        self,
        tenant_id: str,
        *,
        diagnosis_type_id: str,
        diagnosis_id: str | None,
        is_enabled: bool | None = None,
        sort_order: int | None = None,
        local_label: str | None = None,
    ) -> TenantOverlay: ...

    # === Legacy aliases ===

    @abstractmethod
    async def list_aliases(self, *, confidence: str | None = None) -> list[DiagnosisAlias]: ...

    @abstractmethod
    async def upsert_alias(
        self,
        *,
        raw_value: str,
        diagnosis_type_id: str,
        diagnosis_id: str | None,
        source: str,
        confidence: str,
    ) -> DiagnosisAlias: ...

    @abstractmethod
    async def alias_lookup(self) -> dict[str, tuple[str, str | None]]:
        """Normalised key to (type id, diagnosis id), shaped for the importer."""
