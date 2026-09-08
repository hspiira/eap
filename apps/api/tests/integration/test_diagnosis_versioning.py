"""Retirement writes a date, and an edit bumps the version.

``diagnosis_types`` and ``diagnoses`` carry both ``is_active`` and
``effective_until``, and the read queries require the two to agree: a row is
returned only when ``is_active`` is true and ``effective_until`` is null. Before
this, deactivation wrote only ``is_active`` and nothing ever wrote
``effective_until`` or ``version``, so the effective window was a predicate no
code could satisfy and the version counter never moved.

These run against PostgreSQL rather than a mock because the behaviour depends on
the repository's writes and on the ``version`` server default.

Run with MEMBER_TEST_DATABASE_URL pointing at local PostgreSQL.
"""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.infrastructure.models.base import Base
from app.infrastructure.models.diagnosis_model import DiagnosisModel, DiagnosisTypeModel
from app.infrastructure.repositories.diagnosis_repository import DiagnosisRepositoryImpl

TYPE_ID = "type-1"
DIAGNOSIS_ID = "dx-1"


@pytest_asyncio.fixture
async def repo():
    raw_url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Versioning tests require local PostgreSQL")
    schema = "versioning_test_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    tables = [
        Base.metadata.tables[model.__tablename__] for model in (DiagnosisTypeModel, DiagnosisModel)
    ]
    try:
        async with engine.begin() as connection:
            await connection.run_sync(lambda sync: Base.metadata.create_all(sync, tables=tables))
        async with sessions() as session:
            session.add_all(
                [
                    DiagnosisTypeModel(id=TYPE_ID, code="MIH", name="Mental Ill Health"),
                    DiagnosisModel(
                        id=DIAGNOSIS_ID, type_id=TYPE_ID, code="DEPRESSION", name="Depression"
                    ),
                ]
            )
            await session.commit()
        async with sessions() as session:
            yield DiagnosisRepositoryImpl(session)
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


async def test_retiring_a_type_dates_the_retirement(repo):
    retired = await repo.set_type_active(TYPE_ID, is_active=False)

    assert retired is not None
    assert retired.is_active is False
    assert retired.effective_until is not None, "retirement left the effective window open"
    assert [t.code for t in await repo.list_types()] == []


async def test_reactivating_a_type_clears_the_date(repo):
    """A stale date would keep the row filtered out of every read."""
    await repo.set_type_active(TYPE_ID, is_active=False)

    restored = await repo.set_type_active(TYPE_ID, is_active=True)

    assert restored is not None
    assert restored.is_active is True
    assert restored.effective_until is None
    assert [t.code for t in await repo.list_types()] == ["MIH"]


async def test_retiring_a_diagnosis_dates_the_retirement(repo):
    retired = await repo.set_diagnosis_active(DIAGNOSIS_ID, is_active=False)

    assert retired is not None
    assert retired.is_active is False
    assert retired.effective_until is not None
    assert [d.code for d in await repo.list_diagnoses()] == []


async def test_reactivating_a_diagnosis_clears_the_date(repo):
    await repo.set_diagnosis_active(DIAGNOSIS_ID, is_active=False)

    restored = await repo.set_diagnosis_active(DIAGNOSIS_ID, is_active=True)

    assert restored is not None
    assert restored.effective_until is None
    assert [d.code for d in await repo.list_diagnoses()] == ["DEPRESSION"]


async def test_renaming_a_type_bumps_the_version(repo):
    before = await repo.get_type_by_code("MIH")
    assert before is not None

    after = await repo.update_type(TYPE_ID, name="Mental Health")

    assert after is not None
    assert after.name == "Mental Health"
    assert after.version == before.version + 1


async def test_renaming_a_diagnosis_bumps_the_version(repo):
    before = await repo.get_diagnosis_by_code("DEPRESSION")
    assert before is not None

    after = await repo.update_diagnosis(DIAGNOSIS_ID, description="A depressive disorder.")

    assert after is not None
    assert after.version == before.version + 1


async def test_a_patch_that_changes_nothing_does_not_bump_the_version(repo):
    """Otherwise the counter measures requests rather than changes."""
    before = await repo.get_diagnosis_by_code("DEPRESSION")
    assert before is not None

    after = await repo.update_diagnosis(DIAGNOSIS_ID, name="Depression", sort_order=None)

    assert after is not None
    assert after.version == before.version


async def test_renaming_does_not_retire_the_row(repo):
    after = await repo.update_diagnosis(DIAGNOSIS_ID, name="Depressive disorder")

    assert after is not None
    assert after.is_active is True
    assert after.effective_until is None
    assert [d.code for d in await repo.list_diagnoses()] == ["DEPRESSION"]
