"""Transaction behaviour of the queued client import job.

The job runner writes through three transactions: claim, import, outcome.
A failed import must roll back every client it created while still leaving
the job row marked failed. Run with IMPORT_TEST_DATABASE_URL pointing at
local PostgreSQL.
"""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.application.services import client_import_job
from app.application.services.client_import import ImportRepositories
from app.domain.enums import SubscriptionTier, TenantStatus
from app.infrastructure.models.base import Base
from app.infrastructure.models.client_import_job_model import ClientImportJobModel
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.client_alias_repository import ClientAliasRepositoryImpl
from app.infrastructure.repositories.client_repository import ClientRepositoryImpl
from app.infrastructure.repositories.industry_repository import IndustryRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl
from app.shared.handlers.audit_event_handler import AuditEventHandler
from app.shared.utils.generators import generate_cuid

TENANT_ID = "tenant-import-test"
USER_ID = "user-import-test"

CSV_HEADER = (
    "name,code,phone,email,address,billing_street,billing_city,billing_country,"
    "billing_postal_code,industry,parent_client_name,preferred_contact_method,aliases\n"
)


def _csv(*names: str) -> bytes:
    rows = "".join(f"{name},,,,,,,,,,,,\n" for name in names)
    return (CSV_HEADER + rows).encode()


@pytest_asyncio.fixture
async def import_db():
    raw_url = os.environ.get("IMPORT_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set IMPORT_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Client import tests require local PostgreSQL")
    schema = "import_test_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            TenantModel(
                id=TENANT_ID,
                name="Import test tenant",
                code="imprt",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()
    try:
        yield session_factory
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


class _Gateway:
    """The infrastructure wiring the runner takes, bound to the test schema.

    Mirrors _ImportJobGateway in the clients route; the runner itself imports
    no infrastructure.
    """

    def __init__(self, sessions):
        self._sessions = sessions

    def session(self):
        return self._sessions()

    async def load(self, session, job_id: str):
        return await session.get(ClientImportJobModel, job_id)

    def repositories(self, session) -> ImportRepositories:
        return ImportRepositories(
            client=ClientRepositoryImpl(session),
            alias=ClientAliasRepositoryImpl(session),
            industry=IndustryRepositoryImpl(session),
            tenant=TenantRepositoryImpl(session),
        )

    def audit_handler(self, session):
        return AuditEventHandler(OutboxRepositoryImpl(session))


async def _queue_job(session_factory, content: bytes) -> str:
    job_id = generate_cuid()
    async with session_factory() as session:
        session.add(
            ClientImportJobModel(
                id=job_id,
                tenant_id=TENANT_ID,
                requested_by=USER_ID,
                filename="clients.csv",
                file_size=len(content),
                file_content=content,
                decisions={},
                status="queued",
                total_rows=0,
                issues=[],
            )
        )
        await session.commit()
    return job_id


async def _job(session_factory, job_id: str) -> ClientImportJobModel:
    async with session_factory() as session:
        job = await session.get(ClientImportJobModel, job_id)
        assert job is not None
        return job


class TestImportJob:
    async def test_successful_import_creates_clients_and_completes_the_job(self, import_db):
        job_id = await _queue_job(import_db, _csv("Acme Corp", "Globex"))

        await client_import_job.run_import_job(job_id, _Gateway(import_db))

        job = await _job(import_db, job_id)
        assert job.status == "completed"
        assert job.imported == 2
        assert job.failed == 0
        assert job.started_at is not None
        assert job.completed_at is not None
        assert job.error_message is None

        async with import_db() as session:
            names = (await session.execute(select(ClientModel.name))).scalars().all()
            assert sorted(names) == ["Acme Corp", "Globex"]

    @pytest.mark.xfail(
        reason=(
            "ClientEntity emits no creation event, so creating a client is never "
            "audited. The audit machinery already maps a 'created' event to "
            "AuditActionType.CREATE and other entities (CareCallbackCampaign, Case) "
            "emit one from __post_init__. Adding ClientCreated changes audit volume "
            "for every create path, so it needs a decision rather than a drive-by fix."
        ),
        strict=True,
    )
    async def test_audit_events_are_enqueued_in_the_import_transaction(self, import_db):
        job_id = await _queue_job(import_db, _csv("Acme Corp"))

        await client_import_job.run_import_job(job_id, _Gateway(import_db))

        async with import_db() as session:
            events = (await session.execute(select(OutboxEventModel))).scalars().all()
            assert len(events) == 1
            assert events[0].tenant_id == TENANT_ID
            assert events[0].delivered_at is None

    async def test_a_failed_import_rolls_back_every_client_it_created(self, import_db, monkeypatch):
        job_id = await _queue_job(import_db, _csv("Acme Corp", "Globex", "Initech"))

        real_create = client_import_job.client_import.create_clients

        async def explode(*args, **kwargs):
            # Let the first rows be created, then fail the whole import.
            await real_create(*args, **kwargs)
            raise RuntimeError("import blew up after writing rows")

        monkeypatch.setattr(client_import_job.client_import, "create_clients", explode)

        await client_import_job.run_import_job(job_id, _Gateway(import_db))

        job = await _job(import_db, job_id)
        assert job.status == "failed"
        assert job.error_message == "import blew up after writing rows"
        assert job.completed_at is not None

        async with import_db() as session:
            clients = await session.scalar(select(func.count(ClientModel.id)))
            outbox = await session.scalar(select(func.count(OutboxEventModel.id)))
        assert clients == 0, "a failed import must not leave partial clients behind"
        # Zero for two reasons today: the rollback, and the missing creation
        # event covered by the xfail above. Kept so the rollback stays asserted
        # once ClientCreated exists.
        assert outbox == 0, "audit events must roll back with the import"

    async def test_validation_errors_complete_the_job_without_creating_clients(self, import_db):
        # A billing street with no city or country cannot form an Address.
        content = (CSV_HEADER + "Acme Corp,,,,,1 High St,,,,,,,\n").encode()
        job_id = await _queue_job(import_db, content)

        await client_import_job.run_import_job(job_id, _Gateway(import_db))

        job = await _job(import_db, job_id)
        assert job.status == "completed"
        assert job.imported == 0
        assert job.failed == 1
        assert job.issues

        async with import_db() as session:
            assert await session.scalar(select(func.count(ClientModel.id))) == 0

    async def test_a_missing_job_is_ignored(self, import_db):
        await client_import_job.run_import_job("does-not-exist", _Gateway(import_db))
