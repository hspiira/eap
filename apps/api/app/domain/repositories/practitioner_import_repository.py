"""Persistence contract for the staged practitioner workbook import."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.entities.practitioner_import import (
    PractitionerImportBatchEntity,
    PractitionerImportRowEntity,
)
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import PractitionerImportBatchId


class PractitionerImportRepository(ABC):
    @abstractmethod
    async def get_batch(
        self, tenant_id: TenantId, batch_id: PractitionerImportBatchId
    ) -> PractitionerImportBatchEntity | None: ...

    @abstractmethod
    async def find_batch_by_hash(
        self, tenant_id: TenantId, file_hash: str
    ) -> PractitionerImportBatchEntity | None:
        """Used to detect a replay of the same file before staging it again."""

    @abstractmethod
    async def save_batch(self, batch: PractitionerImportBatchEntity) -> None: ...

    @abstractmethod
    async def add_rows(
        self, rows: Sequence[PractitionerImportRowEntity], *, file_hash: str
    ) -> None: ...

    @abstractmethod
    async def list_rows(
        self,
        tenant_id: TenantId,
        batch_id: PractitionerImportBatchId,
        *,
        outcome: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[PractitionerImportRowEntity], int]: ...

    @abstractmethod
    async def find_row_by_replay_key(
        self, tenant_id: TenantId, replay_key: str
    ) -> PractitionerImportRowEntity | None: ...

    @abstractmethod
    async def record_row_apply(self, row: PractitionerImportRowEntity) -> None:
        """Persist a row's apply result: outcome, reasons and created record ids."""

    @abstractmethod
    async def outcome_counts(
        self, tenant_id: TenantId, batch_id: PractitionerImportBatchId
    ) -> dict[str, int]: ...
