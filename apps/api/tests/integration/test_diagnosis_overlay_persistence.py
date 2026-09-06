"""The tenant overlay is a partial update, and reordering depends on that.

Reordering writes only ``sort_order`` for every sibling. If that write also
reset ``is_enabled`` or ``local_label``, moving a row would silently unhide a
row the tenant had hidden, or drop a rename. These run against PostgreSQL
rather than a mock, because the behaviour lives in the repository's merge and
the column defaults.

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

from app.domain.enums import SubscriptionTier, TenantStatus
from app.infrastructure.models.base import Base
from app.infrastructure.models.diagnosis_model import (
    DiagnosisModel,
    DiagnosisTypeModel,
    TenantDiagnosisSettingModel,
)
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.diagnosis_repository import DiagnosisRepositoryImpl

TENANT = "t1"
TYPE_ID = "type-1"
OTHER_TYPE_ID = "type-2"
DIAGNOSIS_ID = "dx-1"


@pytest_asyncio.fixture
async def overlay_repo():
    raw_url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Overlay tests require local PostgreSQL")
    schema = "overlay_test_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    tables = [
        Base.metadata.tables[model.__tablename__]
        for model in (
            TenantModel,
            DiagnosisTypeModel,
            DiagnosisModel,
            TenantDiagnosisSettingModel,
        )
    ]
    try:
        async with engine.begin() as connection:
            await connection.run_sync(lambda sync: Base.metadata.create_all(sync, tables=tables))
        async with sessions() as session:
            session.add_all(
                [
                    TenantModel(
                        id=TENANT,
                        name="Test",
                        code="TEST",
                        settings={},
                        status=TenantStatus.ACTIVE,
                        subscription_tier=SubscriptionTier.FREE,
                    ),
                    DiagnosisTypeModel(id=TYPE_ID, code="MIH", name="Mental Ill Health"),
                    DiagnosisTypeModel(id=OTHER_TYPE_ID, code="GBV", name="GBV"),
                    DiagnosisModel(
                        id=DIAGNOSIS_ID, type_id=TYPE_ID, code="DEPRESSION", name="Depression"
                    ),
                ]
            )
            await session.commit()
        async with sessions() as session:
            yield DiagnosisRepositoryImpl(session), session
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


async def test_reordering_does_not_unhide_a_hidden_row(overlay_repo):
    """The exact sequence the admin page performs: hide, then move."""
    repo, session = overlay_repo
    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, is_enabled=False
    )

    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, sort_order=3
    )

    overlay = await repo.tenant_overlay(TENANT)
    row = overlay[(TYPE_ID, None)]
    assert row.is_enabled is False, "reordering silently unhid a hidden row"
    assert row.sort_order == 3


async def test_reordering_does_not_drop_a_local_label(overlay_repo):
    repo, _ = overlay_repo
    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, local_label="Relationship Abuse"
    )

    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, sort_order=1
    )

    row = (await repo.tenant_overlay(TENANT))[(TYPE_ID, None)]
    assert row.local_label == "Relationship Abuse"
    assert row.sort_order == 1


async def test_a_first_write_of_sort_order_alone_leaves_the_row_visible(overlay_repo):
    """Moving a row that had no overlay yet must not hide it."""
    repo, _ = overlay_repo

    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, sort_order=0
    )

    row = (await repo.tenant_overlay(TENANT))[(TYPE_ID, None)]
    assert row.is_enabled is True
    assert row.sort_order == 0


async def test_sort_order_zero_is_stored_not_treated_as_absent(overlay_repo):
    """0 is a real position: first. A falsy check here would drop it."""
    repo, _ = overlay_repo
    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, sort_order=5
    )

    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, sort_order=0
    )

    assert (await repo.tenant_overlay(TENANT))[(TYPE_ID, None)].sort_order == 0


async def test_a_type_row_and_its_leaf_are_separate_overlay_rows(overlay_repo):
    """Otherwise reordering leaves would collide with reordering types."""
    repo, _ = overlay_repo
    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, sort_order=1
    )
    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=DIAGNOSIS_ID, sort_order=2
    )

    overlay = await repo.tenant_overlay(TENANT)
    assert overlay[(TYPE_ID, None)].sort_order == 1
    assert overlay[(TYPE_ID, DIAGNOSIS_ID)].sort_order == 2


async def test_one_tenants_overlay_is_invisible_to_another(overlay_repo):
    repo, _ = overlay_repo
    await repo.set_tenant_overlay(
        TENANT, diagnosis_type_id=TYPE_ID, diagnosis_id=None, is_enabled=False
    )

    assert await repo.tenant_overlay("some-other-tenant") == {}
