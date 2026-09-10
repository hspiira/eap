import csv
import io
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_client_repository,
    get_clinical_subject_repository,
    get_eligible_member_clinical_link_repository,
    get_eligible_member_repository,
    get_member_import_repository,
    get_member_next_of_kin_repository,
    get_next_of_kin_relationship_repository,
    get_outbox_repository,
    get_service_session_repository,
    get_user_repository,
)
from app.api.routes.members import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.eligible_member import EligibleMember
from app.domain.entities.member_import import MemberImportBatchEntity, MemberImportRowEntity
from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.enums import EligibilityStatus, MemberImportRowOutcome, MemberRelation, TenantRole
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.repositories.eligible_member_repository import MemberRosterStats
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    Email,
    MemberImportBatchId,
    MemberImportRowId,
    MemberNextOfKinId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


def member(member_id="m1", **changes):
    now = utc_now()
    return EligibleMember(
        **{
            "id": EligibleMemberId(member_id),
            "tenant_id": TenantId("t1"),
            "client_id": ClientId("c1"),
            "employer_member_id": member_id,
            "display_label": "Amina Namukasa",
            "relation": MemberRelation.EMPLOYEE,
            "status": EligibilityStatus.ACTIVE,
            "created_at": now,
            "updated_at": now,
            **changes,
        }
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        user=TokenData(user_id="u1", tenant_id="t1", role="Admin"),
        members=AsyncMock(),
        clients=AsyncMock(),
        subjects=AsyncMock(),
        links=AsyncMock(),
        contacts=AsyncMock(),
        relationships=AsyncMock(),
        outbox=AsyncMock(),
        users=AsyncMock(),
        sessions=AsyncMock(),
        imports=AsyncMock(),
        db=AsyncMock(),
    )
    state.members.get_by_id.return_value = member()
    state.members.find_by_employer_member_id.return_value = None
    state.members.find_by_import_source_id.return_value = None
    state.members.find_by_import_source_ids.return_value = {}
    state.members.next_member_sequence.return_value = 1
    state.members.list_for_primary.return_value = []
    state.members.list_all.return_value = []
    state.members.count.return_value = 0
    state.members.find_by_user_id.return_value = None
    state.imports.find_batch_by_hash.return_value = None
    state.imports.find_row_by_replay_key.return_value = None
    state.imports.find_rows_by_replay_keys.return_value = {}
    state.imports.outcome_counts.return_value = {}
    state.imports.list_rows.return_value = ([], 0)
    state.imports.get_batch.return_value = None
    state.imports.get_row.return_value = None
    state.clients.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), name="Acme", code="ACM"
    )
    state.contacts.list_for_member.return_value = []
    state.relationships.get_by_code.return_value = SimpleNamespace(code="Spouse")
    state.sessions.list_all.return_value = []
    state.sessions.count.return_value = 0
    state.users.get_by_id.side_effect = lambda user_id: SimpleNamespace(
        id=user_id,
        tenant_id=TenantId("t1"),
        role=TenantRole.ADMIN,
        deleted_at=None,
    )
    dependencies = {
        get_eligible_member_repository: state.members,
        get_client_repository: state.clients,
        get_clinical_subject_repository: state.subjects,
        get_eligible_member_clinical_link_repository: state.links,
        get_member_next_of_kin_repository: state.contacts,
        get_next_of_kin_relationship_repository: state.relationships,
        get_outbox_repository: state.outbox,
        get_user_repository: state.users,
        get_service_session_repository: state.sessions,
        get_member_import_repository: state.imports,
        get_db: state.db,
    }
    for dependency, value in dependencies.items():
        app.dependency_overrides[dependency] = (lambda v: lambda: v)(value)
    app.dependency_overrides[get_current_user] = lambda: state.user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        state.http = client
        yield state


CREATE = {
    "client_id": "c1",
    "display_label": "Amina",
    "relation": "Employee",
}
CONTACT = {"name": "Grace", "relationship": "Spouse", "phone": "+256700000000", "is_primary": True}


async def test_create_commits_roster_subject_link_and_audit_without_pii(api):
    response = await api.http.post("/members", json=CREATE)
    assert response.status_code == 201, response.text
    api.members.save.assert_awaited_once()
    api.subjects.save.assert_awaited_once()
    api.links.link.assert_awaited_once()
    api.db.commit.assert_awaited_once()
    event = api.outbox.enqueue.call_args.kwargs
    assert event["payload"]["action_type"] == "CREATE"
    assert event["tenant_id"] == "t1"
    assert "Amina" not in str(event)
    assert "clinical_subject_id" not in response.json()


async def test_create_without_a_code_issues_the_next_client_sequence(api):
    api.members.next_member_sequence.return_value = 4

    response = await api.http.post("/members", json=CREATE)

    assert response.status_code == 201, response.text
    assert response.json()["employer_member_id"] == "ACM-004"
    api.members.next_member_sequence.assert_awaited_once()


async def test_create_skips_a_code_already_taken(api):
    api.members.next_member_sequence.return_value = 1
    # Taken, free, then the route and the use case each re-check the issued code.
    api.members.find_by_employer_member_id.side_effect = [member("ACM-001"), None, None, None]

    response = await api.http.post("/members", json=CREATE)

    assert response.status_code == 201, response.text
    assert response.json()["employer_member_id"] == "ACM-002"


async def test_create_rejects_an_explicit_member_code(api):
    response = await api.http.post("/members", json={**CREATE, "employer_member_id": "HR-1"})

    assert response.status_code == 422, response.text
    api.members.next_member_sequence.assert_not_awaited()
    api.members.save.assert_not_awaited()


async def test_create_records_optional_identification_numbers(api):
    response = await api.http.post(
        "/members",
        json={
            **CREATE,
            "staff_number": "EMP-9",
            "national_id": "CM12345",
            "passport_number": "B0987654",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["staff_number"] == "EMP-9"
    assert body["national_id"] == "CM12345"
    assert body["passport_number"] == "B0987654"


async def test_stage_persists_a_batch_and_its_rows(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    api.imports.outcome_counts.return_value = {"New": 1}

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,HR-1,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["row_count"] == 1
    assert body["status"] == "Staged"
    assert body["outcome_counts"] == {"New": 1}
    api.imports.save_batch.assert_awaited_once()
    ((rows,), _) = api.imports.add_rows.call_args
    assert len(rows) == 1
    assert rows[0].outcome == MemberImportRowOutcome.NEW
    assert rows[0].decision == "import"


async def test_stage_accepts_a_day_first_date_of_birth(api):
    """03/04/2026 reads as 3 April, matching the region this importer serves."""
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee,Date of Birth\n"
                b"ACME,HR-1,Amina,03/04/2026\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert rows[0].outcome == MemberImportRowOutcome.NEW
    assert rows[0].date_of_birth == "03/04/2026"


async def test_stage_batches_lookups_instead_of_one_query_per_row(api):
    """3,000+ rows one row at a time was slow enough to time out a serverless function.

    A roster this size overwhelmingly repeats one client code; staging it
    must not re-resolve the client, or re-query membership/replay keys, once
    per row.
    """
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    rows_csv = "\n".join(f"ACME,HR-{n},Employee {n}" for n in range(1, 51))

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                f"Company Code,Staff_ID,Name of Employee\n{rows_csv}\n".encode(),
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert len(rows) == 50
    assert all(row.outcome == MemberImportRowOutcome.NEW for row in rows)
    api.clients.get_by_code.assert_awaited_once()
    api.members.find_by_import_source_ids.assert_awaited_once()
    api.members.find_by_import_source_id.assert_not_awaited()
    api.imports.find_rows_by_replay_keys.assert_awaited_once()
    api.imports.find_row_by_replay_key.assert_not_awaited()


async def test_stage_flags_a_duplicate_row_with_a_default_skip_decision(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    api.members.find_by_import_source_ids.return_value = {"HR-1": member()}

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,HR-1,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert rows[0].outcome == MemberImportRowOutcome.DUPLICATE
    assert rows[0].decision == "skip"
    # Not "key:c1:HR-1": that string is already held by the real member's
    # original import row, and reusing it here would collide on insert.
    assert not rows[0].replay_key.startswith("key:")


async def test_stage_gives_repeated_duplicates_of_the_same_id_distinct_keys(api):
    """Production crash: re-staging a roster with a repeated Staff_ID raised a raw

    UniqueViolationError instead of two clean classifications. Every non-New
    outcome for the same Staff_ID must get its own collision-free key, not
    just the first one.
    """
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    api.members.find_by_import_source_ids.return_value = {"HR-1": member()}

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,HR-1,Amina\nACME,HR-1,Amina Again\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert rows[0].outcome == MemberImportRowOutcome.DUPLICATE
    assert rows[1].outcome == MemberImportRowOutcome.INVALID
    assert rows[0].replay_key != rows[1].replay_key
    assert not rows[0].replay_key.startswith("key:")
    assert not rows[1].replay_key.startswith("key:")


async def test_stage_flags_a_row_still_claimed_by_another_unresolved_batch(api):
    """A batch left Staged from an earlier upload still holds its rows' keys.

    Without a pre-check, a second file staging the same Staff_ID hits the
    (tenant_id, replay_key) unique index at INSERT time: an unhandled
    IntegrityError for the whole file, not a classification of the one row.
    """
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    api.imports.find_rows_by_replay_keys.return_value = {
        "key:c1:HR-1": SimpleNamespace(row_number=7, batch_id=MemberImportBatchId("stuck-batch"))
    }

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,HR-1,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert rows[0].outcome == MemberImportRowOutcome.DUPLICATE
    assert rows[0].decision == "skip"
    assert rows[0].message == "Already staged as row 7 of batch stuck-batch"
    # Not the identity key ("key:c1:HR-1"): that string is already held by the
    # row in the stuck batch, and reusing it here would collide on insert.
    assert rows[0].replay_key.startswith("file:")
    assert rows[0].replay_key.endswith(":row:2")


async def test_stage_imports_a_dependant_with_no_staff_id_of_their_own(api):
    """A dependant is identified by Primary Staff ID, not their own Staff_ID."""
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    api.members.find_by_import_source_ids.return_value = {"AC-1": member("m1")}

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
                b"ACME,,Jane Doe Jr,Child,AC-1\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert rows[0].outcome == MemberImportRowOutcome.NEW
    assert rows[0].decision == "import"


async def test_stage_rejects_a_dependant_with_neither_id(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
                b"ACME,,Jane Doe Jr,Child,\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert rows[0].outcome == MemberImportRowOutcome.INVALID
    assert rows[0].message == "Primary Staff ID is required for a beneficiary"


async def test_stage_does_not_treat_two_id_less_dependants_as_duplicates(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    api.members.find_by_import_source_ids.return_value = {"AC-1": member("m1")}

    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
                b"ACME,,Jane Doe Jr,Child,AC-1\n"
                b"ACME,,John Doe Jr,Child,AC-1\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert [row.outcome for row in rows] == [
        MemberImportRowOutcome.NEW,
        MemberImportRowOutcome.NEW,
    ]


async def test_stage_preserves_the_parser_issue_message(api):
    response = await api.http.post(
        "/members/import",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    ((rows,), _) = api.imports.add_rows.call_args
    assert rows[0].outcome == MemberImportRowOutcome.INVALID
    assert rows[0].message == "Stable Staff_ID is required"


async def test_stage_rejects_restaging_a_file_still_awaiting_a_decision(api):
    api.imports.find_batch_by_hash.return_value = SimpleNamespace(
        id=MemberImportBatchId("b1"), status=ImportBatchStatus.STAGED
    )

    response = await api.http.post(
        "/members/import",
        files={"file": ("members.csv", b"Company Code,Staff_ID,Name of Employee\n", "text/csv")},
    )

    assert response.status_code == 409, response.text
    api.imports.save_batch.assert_not_awaited()
    body = response.json()
    assert body["error"] == "IMPORT_ALREADY_STAGED"
    assert {"field": "batch_id", "message": "b1", "code": None} in body["details"]


async def test_list_import_rows_accepts_the_200_page_size_the_dialog_uses(api):
    """MemberImportDialog.tsx pages through fetchAllRows at limit=200.

    Left at the pagination default (max_limit=100), that request 422s before
    a single row can be shown, so nobody staging a roster of more than one
    page could ever see it. No route test caught this because the mocked
    `imports.list_rows` bypasses FastAPI's query validation entirely.
    """
    api.imports.list_rows.return_value = ([import_row(1)], 1)

    response = await api.http.get("/members/import/b1/rows", params={"limit": 200})

    assert response.status_code == 200, response.text
    assert response.json()["limit"] == 200


def import_row(row_number=1, outcome=MemberImportRowOutcome.NEW, decision="import", **overrides):
    now = utc_now()
    return MemberImportRowEntity(
        id=MemberImportRowId(f"r{row_number}"),
        batch_id=MemberImportBatchId("b1"),
        tenant_id=TenantId("t1"),
        row_number=row_number,
        replay_key=f"key:c1:HR-{row_number}",
        outcome=outcome,
        decision=decision,
        created_at=now,
        client_code="ACME",
        client_id=ClientId("c1"),
        import_source_id=f"HR-{row_number}",
        display_label="Amina" if row_number == 1 else "Bosco",
        **overrides,
    )


def staged_batch(**overrides):
    now = utc_now()
    return MemberImportBatchEntity(
        id=MemberImportBatchId("b1"),
        tenant_id=TenantId("t1"),
        file_name="members.csv",
        file_hash="sha256:abc",
        row_count=2,
        staged_by=UserId("u1"),
        created_at=now,
        updated_at=now,
        **overrides,
    )


async def test_apply_writes_every_importable_row_in_its_own_transaction(api):
    api.imports.get_batch.return_value = staged_batch()
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    rows = [import_row(1), import_row(2)]
    api.imports.list_rows.side_effect = [(rows, 2), ([], 2)]

    response = await api.http.post("/members/import/b1/apply")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["imported"] == 2
    assert body["failed"] == 0
    # Two row-level commits, plus one for the batch's own applied-status write.
    assert api.db.commit.await_count == 3


async def test_apply_keeps_going_after_a_row_fails(api):
    api.imports.get_batch.return_value = staged_batch()
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    rows = [import_row(1), import_row(2)]
    api.imports.list_rows.side_effect = [(rows, 2), ([], 2)]
    saves = {"n": 0}

    async def fail_first(_member):
        saves["n"] += 1
        if saves["n"] == 1:
            raise ValueError("member is not writable")

    api.members.save.side_effect = fail_first

    response = await api.http.post("/members/import/b1/apply")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["imported"] == 1
    assert body["failed"] == 1
    api.imports.mark_row_failed.assert_awaited_once()
    assert api.imports.mark_row_failed.call_args.args[2] == "member is not writable"
    assert api.db.rollback.await_count == 1


async def test_apply_never_overwrites_an_existing_member(api):
    api.imports.get_batch.return_value = staged_batch()
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", code="ACME", tenant_id=TenantId("t1")
    )
    api.members.find_by_import_source_id.return_value = member()
    rows = [import_row(1)]
    api.imports.list_rows.side_effect = [(rows, 1), ([], 1)]

    response = await api.http.post("/members/import/b1/apply")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["imported"] == 0
    assert body["not_importable"] == 1
    api.members.save.assert_not_awaited()


async def test_apply_rejects_a_company_code_outside_the_tenant(api):
    api.imports.get_batch.return_value = staged_batch()
    api.clients.get_by_code.return_value = None
    rows = [import_row(1)]
    api.imports.list_rows.side_effect = [(rows, 1), ([], 1)]

    response = await api.http.post("/members/import/b1/apply")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["not_importable"] == 1
    api.imports.mark_row_failed.assert_awaited_once()
    assert "does not resolve" in api.imports.mark_row_failed.call_args.args[2]


async def test_apply_refuses_a_batch_that_is_not_staged(api):
    api.imports.get_batch.return_value = staged_batch(status=ImportBatchStatus.APPLIED)

    response = await api.http.post("/members/import/b1/apply")

    assert response.status_code == 409, response.text
    api.members.save.assert_not_awaited()


async def test_set_row_decision_rejects_a_duplicate_row(api):
    api.imports.get_row.return_value = import_row(
        1, outcome=MemberImportRowOutcome.DUPLICATE, decision="skip"
    )

    response = await api.http.patch("/members/import/b1/rows/r1", json={"decision": "import"})

    assert response.status_code == 400, response.text
    api.imports.set_row_decision.assert_not_awaited()


async def test_set_row_decision_allows_skipping_a_new_row(api):
    api.imports.get_row.return_value = import_row(1)

    response = await api.http.patch("/members/import/b1/rows/r1", json={"decision": "skip"})

    assert response.status_code == 200, response.text
    assert response.json()["decision"] == "skip"
    api.imports.set_row_decision.assert_awaited_once_with(
        TenantId("t1"), MemberImportRowId("r1"), "skip"
    )


async def test_abandon_releases_the_batch_replay_keys(api):
    api.imports.get_batch.return_value = staged_batch()

    response = await api.http.post("/members/import/b1/abandon", json={"reason": "wrong file"})

    assert response.status_code == 200, response.text
    api.imports.release_replay_keys.assert_awaited_once_with(
        TenantId("t1"), MemberImportBatchId("b1")
    )


async def test_member_import_template_is_server_generated(api):
    response = await api.http.get("/members/import/template")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.splitlines()[0] == (
        "Company Code,Staff_ID,Staff Number,Name of Employee,Email Address,Personal Email,"
        "Date of Birth,Gender,Phone,National ID,Passport Number,Job Title,Job Classification,"
        "Skill,Department,Unit,Contract type,Status,Relation,Primary Staff ID"
    )
    assert "Example Member" in response.text


async def test_member_duplicate_scan_only_matches_exact_client_scoped_ids(api):
    api.members.list_all.return_value = [member("m1"), member("m2", employer_member_id="m1")]

    response = await api.http.get("/members/duplicates")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scanned"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["reason"] == "Same Staff_ID within the same client"


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("post", "/members", CREATE),
        ("patch", "/members/m1", {"phone": "123"}),
        ("post", "/members/m1/suspend", {}),
        ("post", "/members/m1/reinstate", {}),
        ("post", "/members/m1/terminate", {}),
        ("post", "/members/m1/next-of-kin", CONTACT),
        ("patch", "/members/m1/next-of-kin/k1", CONTACT),
        ("delete", "/members/m1/next-of-kin/k1", None),
    ],
)
async def test_viewer_cannot_mutate(api, method, path, payload):
    api.user.role = "Viewer"
    response = await api.http.request(method, path, json=payload)
    assert response.status_code == 403
    api.members.save.assert_not_awaited()
    api.contacts.save.assert_not_awaited()
    api.outbox.enqueue.assert_not_awaited()
    api.db.commit.assert_not_awaited()


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("get", "/members/m1", None),
        ("patch", "/members/m1", {"phone": "123"}),
        ("get", "/members/m1/beneficiaries", None),
        ("get", "/members/m1/next-of-kin", None),
        ("post", "/members/m1/suspend", {}),
        ("post", "/members/m1/next-of-kin", CONTACT),
    ],
)
async def test_other_tenant_member_is_hidden(api, method, path, payload):
    api.members.get_by_id.return_value = member(tenant_id=TenantId("t2"))
    response = await api.http.request(method, path, json=payload)
    assert response.status_code == 404
    api.db.commit.assert_not_awaited()
    api.outbox.enqueue.assert_not_awaited()


async def test_admin_links_and_unlinks_an_explicit_user_account(api):
    response = await api.http.put("/members/m1/account", json={"user_id": "u2"})
    assert response.status_code == 200, response.text
    assert response.json()["user_id"] == "u2"
    api.members.find_by_user_id.assert_awaited_once_with(TenantId("t1"), UserId("u2"))
    response = await api.http.delete("/members/m1/account")
    assert response.status_code == 200, response.text
    assert response.json()["user_id"] is None


async def test_account_link_rejects_cross_tenant_and_duplicate_user(api):
    api.users.get_by_id.side_effect = lambda user_id: SimpleNamespace(
        id=user_id,
        tenant_id=TenantId("t1" if user_id.value == "u1" else "t2"),
        role=TenantRole.ADMIN,
        deleted_at=None,
    )
    assert (await api.http.put("/members/m1/account", json={"user_id": "u2"})).status_code == 404
    api.users.get_by_id.side_effect = lambda user_id: SimpleNamespace(
        id=user_id, tenant_id=TenantId("t1"), role=TenantRole.ADMIN, deleted_at=None
    )
    api.members.find_by_user_id.return_value = member("m2")
    assert (await api.http.put("/members/m1/account", json={"user_id": "u2"})).status_code == 409


async def test_only_admin_can_manage_account_links_and_merges(api):
    api.users.get_by_id.side_effect = lambda user_id: SimpleNamespace(
        id=user_id, tenant_id=TenantId("t1"), role=TenantRole.USER, deleted_at=None
    )
    assert (await api.http.put("/members/m1/account", json={"user_id": "u2"})).status_code == 403
    assert (
        await api.http.post("/members/m1/merge", json={"source_member_id": "m2"})
    ).status_code == 403


async def test_service_history_requires_clinical_scope_and_is_member_scoped(api):
    assert (await api.http.get("/members/m1/sessions")).status_code == 403
    api.user.access_scopes = ["Clinical"]
    response = await api.http.get("/members/m1/sessions", params={"page": 2, "limit": 5})
    assert response.status_code == 200, response.text
    api.sessions.list_all.assert_awaited_once_with(
        tenant_id=TenantId("t1"),
        member_id=EligibleMemberId("m1"),
        limit=5,
        offset=5,
        sort_by="scheduled_at",
        sort_desc=True,
    )


async def test_merge_requires_explicit_same_client_members_and_audits(api):
    api.members.get_by_id.side_effect = lambda member_id: member(member_id.value)
    api.members.merge_into.return_value = {"sessions": 2, "beneficiaries": 1}
    response = await api.http.post("/members/m1/merge", json={"source_member_id": "m2"})
    assert response.status_code == 200, response.text
    assert response.json()["source_member_id"] == "m2"
    assert response.json()["transferred"]["sessions"] == 2
    api.members.merge_into.assert_awaited_once_with(
        TenantId("t1"), EligibleMemberId("m2"), EligibleMemberId("m1")
    )
    event_types = [call.kwargs["event_type"] for call in api.outbox.enqueue.await_args_list]
    assert event_types[-2:] == ["EligibleMemberMerged", "EligibleMemberMergedIntoMember"]


async def test_merge_rejects_self_and_cross_client(api):
    assert (
        await api.http.post("/members/m1/merge", json={"source_member_id": "m1"})
    ).status_code == 422
    api.members.get_by_id.side_effect = lambda member_id: member(
        member_id.value, client_id=ClientId("c2" if member_id.value == "m2" else "c1")
    )
    assert (
        await api.http.post("/members/m1/merge", json={"source_member_id": "m2"})
    ).status_code == 409
    api.members.merge_into.assert_not_awaited()


async def test_foreign_client_rejects_creation(api):
    api.clients.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId("t2"))
    response = await api.http.post("/members", json=CREATE)
    assert response.status_code == 404
    api.members.save.assert_not_awaited()


@pytest.mark.parametrize("changes", [{"client_id": ClientId("c2")}, {"tenant_id": TenantId("t2")}])
async def test_beneficiary_primary_must_share_client_and_tenant(api, changes):
    api.members.get_by_id.return_value = member(**changes)
    response = await api.http.post(
        "/members", json={**CREATE, "relation": "Child", "primary_employee_member_id": "m1"}
    )
    assert response.status_code == 422
    api.members.save.assert_not_awaited()


async def test_update_clears_optional_fields_and_preserves_others(api):
    api.members.get_by_id.return_value = member(work_email=Email("amina@example.com"), phone="123")
    response = await api.http.patch("/members/m1", json={"phone": None})
    assert response.status_code == 200, response.text
    assert response.json()["phone"] is None
    assert response.json()["work_email"] == "amina@example.com"
    api.db.commit.assert_awaited_once()


async def test_duplicate_company_id_update_conflicts(api):
    api.members.find_by_employer_member_id.return_value = member("m2")
    response = await api.http.patch("/members/m1", json={"employer_member_id": "m2"})
    assert response.status_code == 409
    api.members.save.assert_not_awaited()
    api.db.rollback.assert_awaited_once()


async def test_employee_with_beneficiaries_cannot_change_relationship(api):
    api.members.list_for_primary.return_value = [member("child")]
    response = await api.http.patch(
        "/members/m1", json={"relation": "Child", "primary_employee_member_id": "m2"}
    )
    assert response.status_code == 409
    api.members.save.assert_not_awaited()


async def test_self_parent_is_rejected(api):
    response = await api.http.patch(
        "/members/m1", json={"relation": "Child", "primary_employee_member_id": "m1"}
    )
    assert response.status_code == 422


async def test_partial_relationship_change_requires_primary(api):
    response = await api.http.patch("/members/m1", json={"relation": "Child"})
    assert response.status_code == 422
    api.members.save.assert_not_awaited()


@pytest.mark.parametrize(
    "action,initial,expected",
    [
        ("suspend", EligibilityStatus.ACTIVE, "Suspended"),
        ("reinstate", EligibilityStatus.SUSPENDED, "Active"),
        ("terminate", EligibilityStatus.ACTIVE, "Terminated"),
    ],
)
async def test_lifecycle_commits_and_audits(api, action, initial, expected):
    api.members.get_by_id.return_value = member(status=initial)
    response = await api.http.post(f"/members/m1/{action}")
    assert response.status_code == 200
    assert response.json()["status"] == expected
    api.db.commit.assert_awaited_once()
    api.outbox.enqueue.assert_awaited_once()


async def test_terminated_member_cannot_reinstate(api):
    api.members.get_by_id.return_value = member(status=EligibilityStatus.TERMINATED)
    response = await api.http.post("/members/m1/reinstate")
    assert response.status_code == 400
    api.db.rollback.assert_awaited_once()


async def test_audit_failure_rolls_back_mutation(api):
    api.outbox.enqueue.side_effect = RuntimeError("outbox unavailable")
    response = await api.http.post("/members/m1/suspend")
    assert response.status_code == 500
    api.db.commit.assert_not_awaited()
    api.db.rollback.assert_awaited_once()


async def test_selected_export_is_scoped_deduplicated_and_spreadsheet_safe(api):
    api.members.get_by_id.side_effect = [
        member(display_label="=1+1"),
        member("m2", tenant_id=TenantId("t2")),
    ]
    response = await api.http.get(
        "/members/export", params=[("member_ids", "m1"), ("member_ids", "m1"), ("member_ids", "m2")]
    )
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 1
    assert rows[0]["display_label"] == "'=1+1"
    assert rows[0]["relation"] == "Employee"
    assert rows[0]["status"] == "Active"
    assert api.members.get_by_id.await_count == 2


async def test_export_fetches_every_page(api):
    api.members.list_all.side_effect = [[member(str(i)) for i in range(1000)], [member("last")]]
    response = await api.http.get("/members/export", params={"client_id": "c1", "status": "Active"})
    assert len(list(csv.DictReader(io.StringIO(response.text)))) == 1001
    assert api.members.list_all.call_args.kwargs["offset"] == 1000
    assert api.members.list_all.call_args.kwargs["client_id"] == ClientId("c1")


async def test_member_response_reports_coverage_and_eligibility(api):
    response = await api.http.get("/members/m1")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["coverage_start"] is None
    assert body["coverage_end"] is None
    assert body["is_currently_eligible"] is True


@pytest.mark.parametrize(
    "changes",
    [
        {"status": EligibilityStatus.TERMINATED},
        {"coverage_end": date(2020, 1, 1)},
        {"coverage_start": date(2999, 1, 1)},
    ],
)
async def test_member_outside_coverage_or_lifecycle_is_not_eligible(api, changes):
    api.members.get_by_id.return_value = member(**changes)
    response = await api.http.get("/members/m1")
    assert response.status_code == 200, response.text
    assert response.json()["is_currently_eligible"] is False


async def test_stats_route_is_not_swallowed_by_the_member_id_route(api):
    api.members.count_by_status.return_value = MemberRosterStats(by_status={}, with_account=0)
    response = await api.http.get("/members/stats")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "total": 0,
        "active": 0,
        "suspended": 0,
        "pending": 0,
        "terminated": 0,
        "with_account": 0,
    }
    api.members.get_by_id.assert_not_awaited()


async def test_stats_maps_counts_and_passes_the_list_filters(api):
    api.members.count_by_status.return_value = MemberRosterStats(
        by_status={
            EligibilityStatus.ACTIVE: 3,
            EligibilityStatus.SUSPENDED: 2,
            EligibilityStatus.PENDING: 1,
            EligibilityStatus.TERMINATED: 4,
        },
        with_account=5,
    )
    response = await api.http.get(
        "/members/stats",
        params={"client_id": "c1", "status": "Active", "relation": "Child", "search": "amina"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "total": 10,
        "active": 3,
        "suspended": 2,
        "pending": 1,
        "terminated": 4,
        "with_account": 5,
    }
    api.members.count_by_status.assert_awaited_once_with(
        TenantId("t1"),
        client_id=ClientId("c1"),
        status=EligibilityStatus.ACTIVE,
        relation=MemberRelation.CHILD,
        search="amina",
    )


async def test_list_scopes_filters_and_rejects_unknown_sort(api):
    response = await api.http.get("/members", params={"client_id": "c1", "relation": "Child"})
    assert response.status_code == 200
    assert api.members.list_all.call_args.args == (TenantId("t1"),)
    assert api.members.list_all.call_args.kwargs["relation"] == MemberRelation.CHILD
    response = await api.http.get("/members", params={"sort_by": "phone"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "method,path,payload,action",
    [
        ("post", "/members/m1/next-of-kin", CONTACT, "CREATE"),
        ("patch", "/members/m1/next-of-kin/k1", CONTACT, "UPDATE"),
        ("delete", "/members/m1/next-of-kin/k1", None, "DELETE"),
    ],
)
async def test_contact_mutations_commit_with_audit(api, method, path, payload, action):
    now = utc_now()
    api.contacts.get_by_id.return_value = MemberNextOfKin(
        MemberNextOfKinId("k1"),
        TenantId("t1"),
        EligibleMemberId("m1"),
        "Grace",
        "Spouse",
        "123",
        None,
        False,
        now,
        now,
    )
    response = await api.http.request(method, path, json=payload)
    assert response.status_code in {200, 201, 204}, response.text
    api.db.commit.assert_awaited_once()
    event = api.outbox.enqueue.call_args.kwargs["payload"]
    assert event["action_type"] == action
    assert event["event_data"] == {"member_id": "m1"}
    assert "Grace" not in str(event)


@pytest.mark.parametrize("method", ["patch", "delete"])
async def test_contact_cannot_be_accessed_through_another_member(api, method):
    now = utc_now()
    api.contacts.get_by_id.return_value = MemberNextOfKin(
        MemberNextOfKinId("k1"),
        TenantId("t1"),
        EligibleMemberId("m2"),
        "Grace",
        "Spouse",
        "123",
        None,
        False,
        now,
        now,
    )
    response = await api.http.request(
        method, "/members/m1/next-of-kin/k1", json=CONTACT if method == "patch" else None
    )
    assert response.status_code == 404
    api.db.commit.assert_not_awaited()
