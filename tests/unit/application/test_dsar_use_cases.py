"""DSAR use case tests with fakes (Phase 4 #DSAR)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.application.use_cases.dsar_use_cases import (
    CancelErasureUseCase,
    ExecuteErasureUseCase,
    ExecuteExportUseCase,
    RequestErasureUseCase,
    RequestExportUseCase,
)
from app.domain.entities.dsar_request import DSARRequest
from app.domain.enums import DSARRequestStatus
from app.domain.events import DSARErasureExecuted
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
    UserId,
)


class _FakeRepo:
    def __init__(self):
        self.store: dict[str, DSARRequest] = {}

    async def get_by_id(self, rid):
        return self.store.get(rid.value)

    async def save(self, entity):
        self.store[entity.id.value] = entity

    async def delete(self, rid):
        self.store.pop(rid.value, None)

    async def exists(self, rid):
        return rid.value in self.store

    async def list_for_tenant(self, tenant_id, *, limit=100, offset=0):
        return [r for r in self.store.values() if r.tenant_id == tenant_id]

    async def list_for_subject(self, tenant_id, subject_person_id):
        return [
            r
            for r in self.store.values()
            if r.tenant_id == tenant_id
            and r.subject_person_id == subject_person_id
        ]


class _FakeCollector:
    def __init__(self, *, fail: bool = False):
        self.fail = fail

    async def collect(self, *, tenant_id, subject_person_id) -> dict[str, Any]:
        if self.fail:
            raise RuntimeError("collector boom")
        return {
            "subject": subject_person_id.value,
            "tenant": tenant_id.value,
            "fixtures": [],
        }


class _FakeTombstoner:
    def __init__(self, *, token: str = "tok-abc", fail: bool = False):
        self.token = token
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    async def tombstone(self, *, tenant_id, subject_person_id) -> str:
        if self.fail:
            raise RuntimeError("tombstone boom")
        self.calls.append((tenant_id.value, subject_person_id.value))
        return self.token


# ---------- Export ----------


class TestExport:
    @pytest.mark.asyncio
    async def test_request_then_execute_completes(self):
        repo = _FakeRepo()
        req = await RequestExportUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
        )
        assert req.status == DSARRequestStatus.REQUESTED
        out = await ExecuteExportUseCase(repo, _FakeCollector()).execute(
            DSARRequestId("r-1")
        )
        assert out.status == DSARRequestStatus.COMPLETED
        assert out.output is not None
        assert out.output["subject"] == "p-1"

    @pytest.mark.asyncio
    async def test_collection_failure_marks_request_failed(self):
        repo = _FakeRepo()
        await RequestExportUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
        )
        with pytest.raises(RuntimeError):
            await ExecuteExportUseCase(repo, _FakeCollector(fail=True)).execute(
                DSARRequestId("r-1")
            )
        assert repo.store["r-1"].status == DSARRequestStatus.FAILED
        assert "collector boom" in (repo.store["r-1"].failed_reason or "")

    @pytest.mark.asyncio
    async def test_execute_unknown_request(self):
        with pytest.raises(NotFoundError):
            await ExecuteExportUseCase(_FakeRepo(), _FakeCollector()).execute(
                DSARRequestId("nope")
            )

    @pytest.mark.asyncio
    async def test_execute_export_rejects_erasure(self):
        repo = _FakeRepo()
        await RequestErasureUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
        )
        with pytest.raises(DomainError, match="EXPORT"):
            await ExecuteExportUseCase(repo, _FakeCollector()).execute(
                DSARRequestId("r-1")
            )


# ---------- Erasure ----------


class TestErasure:
    @pytest.mark.asyncio
    async def test_request_sets_reversible_window(self):
        repo = _FakeRepo()
        req = await RequestErasureUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
            reversible_window_days=7,
        )
        assert req.erasure_executes_at is not None
        assert req.is_within_reversible_window()

    @pytest.mark.asyncio
    async def test_cannot_execute_during_reversible_window(self):
        repo = _FakeRepo()
        await RequestErasureUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
            reversible_window_days=14,
        )
        with pytest.raises(DomainError, match="reversible window"):
            await ExecuteErasureUseCase(repo, _FakeTombstoner()).execute(
                DSARRequestId("r-1")
            )

    @pytest.mark.asyncio
    async def test_executes_after_window(self):
        repo = _FakeRepo()
        await RequestErasureUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
            reversible_window_days=14,
        )
        # Hand-jam the deadline into the past to simulate the window elapsing.
        req = repo.store["r-1"]
        req.erasure_executes_at = datetime.now(UTC) - timedelta(seconds=1)
        tomb = _FakeTombstoner(token="abc123")
        out = await ExecuteErasureUseCase(repo, tomb).execute(
            DSARRequestId("r-1")
        )
        assert out.status == DSARRequestStatus.COMPLETED
        assert out.output == {"tombstone_token": "abc123"}
        assert tomb.calls == [("t-1", "p-1")]
        assert any(isinstance(e, DSARErasureExecuted) for e in out.events)

    @pytest.mark.asyncio
    async def test_cancel_within_window(self):
        repo = _FakeRepo()
        await RequestErasureUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
            reversible_window_days=10,
        )
        out = await CancelErasureUseCase(repo).execute(DSARRequestId("r-1"))
        assert out.status == DSARRequestStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_tombstoner_failure_marks_failed(self):
        repo = _FakeRepo()
        await RequestErasureUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
            reversible_window_days=14,
        )
        repo.store["r-1"].erasure_executes_at = datetime.now(UTC) - timedelta(
            seconds=1
        )
        with pytest.raises(RuntimeError):
            await ExecuteErasureUseCase(repo, _FakeTombstoner(fail=True)).execute(
                DSARRequestId("r-1")
            )
        assert repo.store["r-1"].status == DSARRequestStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_erasure_rejects_export(self):
        repo = _FakeRepo()
        await RequestExportUseCase(repo).execute(
            request_id=DSARRequestId("r-1"),
            tenant_id=TenantId("t-1"),
            subject_person_id=PersonId("p-1"),
            requested_by=UserId("u-1"),
        )
        with pytest.raises(DomainError, match="ERASURE"):
            await ExecuteErasureUseCase(repo, _FakeTombstoner()).execute(
                DSARRequestId("r-1")
            )
