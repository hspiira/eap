"""Persistence contract for staged member roster imports."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.entities.member_import import MemberImportBatchEntity, MemberImportRowEntity
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId


class MemberImportRepository(ABC):
    @abstractmethod
    async def get_batch(
        self, tenant_id: TenantId, batch_id: MemberImportBatchId
    ) -> MemberImportBatchEntity | None: ...

    @abstractmethod
    async def find_batch_by_hash(
        self, tenant_id: TenantId, file_hash: str
    ) -> MemberImportBatchEntity | None:
        """Used to detect a replay of the same file before staging it again."""

    @abstractmethod
    async def save_batch(self, batch: MemberImportBatchEntity) -> None: ...

    @abstractmethod
    async def add_rows(self, rows: Sequence[MemberImportRowEntity]) -> None: ...

    @abstractmethod
    async def get_row(
        self, tenant_id: TenantId, batch_id: MemberImportBatchId, row_id: MemberImportRowId
    ) -> MemberImportRowEntity | None: ...

    @abstractmethod
    async def list_rows(
        self,
        tenant_id: TenantId,
        batch_id: MemberImportBatchId,
        *,
        outcome: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[MemberImportRowEntity], int]: ...

    @abstractmethod
    async def set_row_decision(
        self, tenant_id: TenantId, row_id: MemberImportRowId, decision: str
    ) -> None:
        """Record a person's Import/Skip override for one still-new row."""

    @abstractmethod
    async def mark_row_imported(
        self, tenant_id: TenantId, row_id: MemberImportRowId, member_id: str
    ) -> None:
        """Record which member a staged row produced.

        An update, not a second insert: the row already exists and its replay
        key is unique per tenant.
        """

    @abstractmethod
    async def mark_row_failed(
        self, tenant_id: TenantId, row_id: MemberImportRowId, message: str
    ) -> None:
        """Record that writing an importable row raised. Terminal, never retried."""

    @abstractmethod
    async def release_replay_keys(self, tenant_id: TenantId, batch_id: MemberImportBatchId) -> int:
        """Stop an abandoned batch's rows claiming their Staff IDs.

        A replay key says "this roster row has been imported". Rows of a
        batch nobody will apply imported nothing, and while they hold their
        keys the same roster cannot be staged again.
        """

    @abstractmethod
    async def release_superseded_rows(self, tenant_id: TenantId, file_hash: str) -> int:
        """Stop earlier stagings of this same file claiming rows they never imported."""

    @abstractmethod
    async def find_row_by_replay_key(
        self, tenant_id: TenantId, replay_key: str
    ) -> MemberImportRowEntity | None: ...

    @abstractmethod
    async def find_rows_by_replay_keys(
        self, tenant_id: TenantId, replay_keys: list[str]
    ) -> dict[str, MemberImportRowEntity]:
        """Every live row among the given keys, keyed by that key.

        Batches what would otherwise be one `find_row_by_replay_key` call
        per roster row.
        """

    @abstractmethod
    async def outcome_counts(
        self, tenant_id: TenantId, batch_id: MemberImportBatchId
    ) -> dict[str, int]: ...
