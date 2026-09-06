"""Client list employee counts use the canonical member roster."""

from unittest.mock import AsyncMock

from sqlalchemy import create_engine

from app.api.routes.clients import _client_list_metrics
from app.domain.enums import EligibilityStatus, MemberRelation
from app.infrastructure.models.eligible_member_model import EligibleMemberModel


async def test_employee_counts_are_tenant_and_page_scoped() -> None:
    engine = create_engine("sqlite://")
    table = EligibleMemberModel.__table__
    try:
        table.create(engine)
        with engine.begin() as connection:
            records = [
                ("tenant-1", "client-1", MemberRelation.EMPLOYEE, status)
                for status in EligibilityStatus
            ] + [
                ("tenant-1", "client-1", MemberRelation.CHILD, EligibilityStatus.ACTIVE),
                ("tenant-1", "client-2", MemberRelation.EMPLOYEE, EligibilityStatus.ACTIVE),
                ("tenant-2", "client-1", MemberRelation.EMPLOYEE, EligibilityStatus.ACTIVE),
                ("tenant-1", "off-page", MemberRelation.EMPLOYEE, EligibilityStatus.ACTIVE),
            ]
            connection.execute(
                table.insert(),
                [
                    dict(
                        id=f"member-{index}",
                        tenant_id=tenant,
                        client_id=client,
                        employer_member_id=str(index),
                        relation=relation,
                        status=status,
                    )
                    for index, (tenant, client, relation, status) in enumerate(records)
                ],
            )

            async def execute(statement):
                if statement.get_final_froms() == [table]:
                    return connection.execute(statement).all()
                return []

            db = AsyncMock(execute=AsyncMock(side_effect=execute))
            metrics = await _client_list_metrics(
                db, "tenant-1", ["client-1", "client-2", "empty-client"]
            )

        assert metrics["client-1"]["staff_count"] == len(EligibilityStatus)
        assert metrics["client-2"]["staff_count"] == 1
        assert metrics["empty-client"]["staff_count"] == 0
        assert set(metrics) == {"client-1", "client-2", "empty-client"}
    finally:
        engine.dispose()


async def test_empty_client_page_does_not_query_metrics() -> None:
    db = AsyncMock()
    assert await _client_list_metrics(db, "tenant-1", []) == {}
    db.execute.assert_not_awaited()
