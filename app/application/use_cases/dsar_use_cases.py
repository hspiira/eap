"""DSAR use cases (Phase 4 #DSAR / SAD §6.6 / §8.4).

The aggregate (``DSARRequest``) tracks lifecycle. These use cases orchestrate
collection (export) and tombstoning (erasure) via the protocols defined in
``app.application.services.dsar_service``.

Erasure path:
    1. ``RequestErasure`` creates the request with an ``erasure_executes_at``
       deadline (now + reversible window).
    2. The subject can ``cancel`` until the deadline elapses.
    3. ``ExecuteErasure`` performs the tombstoning *only* when the deadline has
       passed; running earlier is a domain error so the cancel guarantee is
       preserved.
"""

from __future__ import annotations

from datetime import timedelta

from app.application.services.dsar_service import (
    DSARDataCollector,
    DSARTombstoner,
)
from app.application.use_cases.base import BaseUseCase
from app.domain.entities.dsar_request import DSARRequest
from app.domain.enums import DSARRequestStatus, DSARRequestType
from app.domain.events import DSARErasureExecuted
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.dsar_repository import DSARRequestRepository
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
    UserId,
)
from app.domain.value_objects.retention import ERASURE_REVERSIBLE_WINDOW_DAYS
from app.shared.utils.datetime import utc_now


class RequestExportUseCase(BaseUseCase[DSARRequest, DSARRequestId]):
    def __init__(self, repository: DSARRequestRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        request_id: DSARRequestId,
        tenant_id: TenantId,
        subject_person_id: PersonId,
        requested_by: UserId,
    ) -> DSARRequest:
        now = utc_now()
        req = DSARRequest(
            id=request_id,
            tenant_id=tenant_id,
            subject_person_id=subject_person_id,
            request_type=DSARRequestType.EXPORT,
            status=DSARRequestStatus.REQUESTED,
            requested_by=requested_by,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(req)


class ExecuteExportUseCase:
    """Drive an EXPORT request through PROCESSING → COMPLETED with the bundle attached."""

    def __init__(
        self,
        repository: DSARRequestRepository,
        collector: DSARDataCollector,
    ):
        self._repo = repository
        self._collector = collector

    async def execute(self, request_id: DSARRequestId) -> DSARRequest:
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise NotFoundError(
                f"DSAR request not found: {request_id.value}",
                resource_type="DSARRequest",
                resource_id=request_id.value,
            )
        if req.request_type != DSARRequestType.EXPORT:
            raise DomainError("ExecuteExportUseCase only handles EXPORT requests")
        req.start()
        await self._repo.save(req)
        try:
            bundle = await self._collector.collect(
                tenant_id=req.tenant_id,
                subject_person_id=req.subject_person_id,
            )
        except Exception as exc:
            req.fail(f"Collection failed: {exc}")
            await self._repo.save(req)
            raise
        req.complete(bundle)
        await self._repo.save(req)
        return req


class RequestErasureUseCase(BaseUseCase[DSARRequest, DSARRequestId]):
    """Submit an erasure request with a reversible-window deadline."""

    def __init__(self, repository: DSARRequestRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        request_id: DSARRequestId,
        tenant_id: TenantId,
        subject_person_id: PersonId,
        requested_by: UserId,
        reversible_window_days: int = ERASURE_REVERSIBLE_WINDOW_DAYS,
    ) -> DSARRequest:
        if reversible_window_days < 0:
            raise DomainError("reversible_window_days cannot be negative")
        now = utc_now()
        req = DSARRequest(
            id=request_id,
            tenant_id=tenant_id,
            subject_person_id=subject_person_id,
            request_type=DSARRequestType.ERASURE,
            status=DSARRequestStatus.REQUESTED,
            requested_by=requested_by,
            erasure_executes_at=now + timedelta(days=reversible_window_days),
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(req)


class CancelErasureUseCase:
    def __init__(self, repository: DSARRequestRepository):
        self._repo = repository

    async def execute(self, request_id: DSARRequestId) -> DSARRequest:
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise NotFoundError(
                f"DSAR request not found: {request_id.value}",
                resource_type="DSARRequest",
                resource_id=request_id.value,
            )
        req.cancel()
        await self._repo.save(req)
        return req


class ExecuteErasureUseCase:
    """Tombstone subject PII once the reversible window has elapsed."""

    def __init__(
        self,
        repository: DSARRequestRepository,
        tombstoner: DSARTombstoner,
    ):
        self._repo = repository
        self._tombstoner = tombstoner

    async def execute(self, request_id: DSARRequestId) -> DSARRequest:
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise NotFoundError(
                f"DSAR request not found: {request_id.value}",
                resource_type="DSARRequest",
                resource_id=request_id.value,
            )
        if req.request_type != DSARRequestType.ERASURE:
            raise DomainError("ExecuteErasureUseCase only handles ERASURE requests")
        if req.is_within_reversible_window():
            raise DomainError(
                "Cannot execute erasure during the reversible window"
            )
        req.start()
        await self._repo.save(req)
        try:
            tombstone_token = await self._tombstoner.tombstone(
                tenant_id=req.tenant_id,
                subject_person_id=req.subject_person_id,
            )
        except Exception as exc:
            req.fail(f"Tombstoning failed: {exc}")
            await self._repo.save(req)
            raise
        req.complete({"tombstone_token": tombstone_token})
        req.events.append(
            DSARErasureExecuted(
                occurred_at=utc_now(),
                request_id=req.id,
                subject_person_id=req.subject_person_id,
                tombstone_token=tombstone_token,
            )
        )
        await self._repo.save(req)
        return req
