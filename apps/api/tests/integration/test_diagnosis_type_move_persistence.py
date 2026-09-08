"""Moving a diagnosis between types persists, and does not rewrite history.

The catalogue in docs/TAXONOMY_CATALOGUE.md moves ``CAREER_FATIGUE`` from
``WORK_STRESS_ANXIETY`` to ``CAREER_CHALLENGES``, and before this there was no
write path that could. A session records ``diagnosis_type_id`` and
``diagnosis_id`` independently, so moving the taxonomy leaf leaves an existing
session reporting the type it was recorded against.

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

WORK = "type-work"
CAREER = "type-career"
DIAGNOSIS_ID = "dx-fatigue"


@pytest_asyncio.fixture
async def repo():
    raw_url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Move tests require local PostgreSQL")
    schema = "move_test_" + uuid4().hex
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
                    DiagnosisTypeModel(
                        id=WORK, code="WORK_STRESS_ANXIETY", name="Work Stress / Anxiety"
                    ),
                    DiagnosisTypeModel(
                        id=CAREER, code="CAREER_CHALLENGES", name="Career Challenges"
                    ),
                    DiagnosisModel(
                        id=DIAGNOSIS_ID,
                        type_id=WORK,
                        code="CAREER_FATIGUE",
                        name="Career fatigue",
                        description="Loss of motivation in the career itself.",
                        sort_order=3,
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


async def test_a_diagnosis_can_be_moved_to_another_type(repo):
    moved = await repo.update_diagnosis(DIAGNOSIS_ID, type_id=CAREER)

    assert moved is not None
    assert moved.type_id == CAREER
    assert [d.code for d in await repo.list_diagnoses(type_code="CAREER_CHALLENGES")] == [
        "CAREER_FATIGUE"
    ]
    assert await repo.list_diagnoses(type_code="WORK_STRESS_ANXIETY") == []


async def test_a_move_leaves_the_other_fields_alone(repo):
    """A move is a reparent, not a reset: the leaf keeps its identity."""
    moved = await repo.update_diagnosis(DIAGNOSIS_ID, type_id=CAREER)

    assert moved is not None
    assert moved.code == "CAREER_FATIGUE"
    assert moved.name == "Career fatigue"
    assert moved.description == "Loss of motivation in the career itself."
    assert moved.sort_order == 3
    assert moved.is_active is True
    assert moved.effective_until is None


async def test_a_move_bumps_the_version(repo):
    before = await repo.get_diagnosis_by_code("CAREER_FATIGUE")
    assert before is not None

    moved = await repo.update_diagnosis(DIAGNOSIS_ID, type_id=CAREER)

    assert moved is not None
    assert moved.version == before.version + 1


async def test_moving_to_the_same_type_is_not_a_change(repo):
    before = await repo.get_diagnosis_by_code("CAREER_FATIGUE")
    assert before is not None

    unmoved = await repo.update_diagnosis(DIAGNOSIS_ID, type_id=WORK)

    assert unmoved is not None
    assert unmoved.type_id == WORK
    assert unmoved.version == before.version


async def test_a_move_and_a_rename_in_one_patch(repo):
    """The catalogue import does both to this row, in one call."""
    moved = await repo.update_diagnosis(DIAGNOSIS_ID, type_id=CAREER, name="Career fatigue (role)")

    assert moved is not None
    assert moved.type_id == CAREER
    assert moved.name == "Career fatigue (role)"
