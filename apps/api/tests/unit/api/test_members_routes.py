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
    get_member_next_of_kin_repository,
    get_outbox_repository,
    get_service_session_repository,
    get_user_repository,
)
from app.api.routes.members import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.eligible_member import EligibleMember
from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.enums import EligibilityStatus, MemberRelation, NextOfKinRelationship, TenantRole
from app.domain.repositories.eligible_member_repository import MemberRosterStats
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    Email,
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
        outbox=AsyncMock(),
        users=AsyncMock(),
        sessions=AsyncMock(),
        db=AsyncMock(),
    )
    state.members.get_by_id.return_value = member()
    state.members.find_by_employer_member_id.return_value = None
    state.members.list_for_primary.return_value = []
    state.members.list_all.return_value = []
    state.members.count.return_value = 0
    state.members.find_by_user_id.return_value = None
    state.clients.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), name="Acme", code="ACM"
    )
    state.contacts.list_for_member.return_value = []
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
        get_outbox_repository: state.outbox,
        get_user_repository: state.users,
        get_service_session_repository: state.sessions,
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
    "employer_member_id": "HR-1",
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
    payload = {key: value for key, value in CREATE.items() if key != "employer_member_id"}

    response = await api.http.post("/members", json=payload)

    assert response.status_code == 201, response.text
    assert response.json()["employer_member_id"] == "ACM-004"
    api.members.next_member_sequence.assert_awaited_once()


async def test_create_skips_a_code_already_taken(api):
    api.members.next_member_sequence.return_value = 1
    # Taken, free, then the route and the use case each re-check the issued code.
    api.members.find_by_employer_member_id.side_effect = [member("ACM-001"), None, None, None]
    payload = {key: value for key, value in CREATE.items() if key != "employer_member_id"}

    response = await api.http.post("/members", json=payload)

    assert response.status_code == 201, response.text
    assert response.json()["employer_member_id"] == "ACM-002"


async def test_create_keeps_an_explicit_member_code(api):
    response = await api.http.post("/members", json=CREATE)

    assert response.status_code == 201, response.text
    assert response.json()["employer_member_id"] == "HR-1"
    api.members.next_member_sequence.assert_not_awaited()


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


async def test_roster_preview_exposes_duplicate_as_safe_default_skip(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", tenant_id=TenantId("t1")
    )
    api.members.find_by_employer_member_id.return_value = member()

    response = await api.http.post(
        "/members/import?dry_run=true",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,HR-1,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["imported"] == 0
    assert body["skipped"] == 1
    assert body["rows"][0]["state"] == "duplicate"
    assert body["rows"][0]["default_action"] == "skip"


async def test_roster_preview_honours_explicit_skip_for_new_rows(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", tenant_id=TenantId("t1")
    )

    response = await api.http.post(
        "/members/import?dry_run=true",
        data={"decisions_json": '{"2":"skip"}'},
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,HR-1,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["imported"] == 0
    assert body["skipped"] == 1
    assert body["rows"][0]["state"] == "skipped"


async def test_roster_preview_preserves_parser_issue_fields(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", tenant_id=TenantId("t1")
    )
    response = await api.http.post(
        "/members/import?dry_run=true",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["issues"] == [
        {"row": 2, "field": "Staff_ID", "message": "Stable Staff_ID is required"}
    ]


def commit_row(row=2, **values):
    return {
        "row": row,
        "values": {
            "client_code": "ACME",
            "employer_member_id": "HR-1",
            "display_label": "Amina",
            **values,
        },
    }


async def test_roster_preview_returns_the_values_the_commit_step_replays(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", tenant_id=TenantId("t1")
    )

    response = await api.http.post(
        "/members/import?dry_run=true",
        files={
            "file": (
                "members.csv",
                b"Company Code,Staff_ID,Name of Employee\nACME,HR-1,Amina\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["rows"][0]["values"] == {
        "client_code": "ACME",
        "employer_member_id": "HR-1",
        "staff_number": None,
        "display_label": "Amina",
        "work_email": None,
        "personal_email": None,
        "gender": None,
        "date_of_birth": None,
        "phone": None,
        "national_id": None,
        "passport_number": None,
        "status": None,
        "relation": None,
        "primary_employee_member_id": None,
    }


async def test_import_commit_writes_every_row_in_its_own_transaction(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", tenant_id=TenantId("t1")
    )

    response = await api.http.post(
        "/members/import/commit",
        json={
            "rows": [
                commit_row(2),
                commit_row(3, employer_member_id="HR-2", display_label="Bosco"),
            ]
        },
    )

    assert response.status_code == 200, response.text
    assert [row["state"] for row in response.json()["results"]] == ["imported", "imported"]
    assert api.db.commit.await_count == 2


async def test_import_commit_keeps_going_after_a_row_fails(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", tenant_id=TenantId("t1")
    )
    saves = {"n": 0}

    async def fail_first(_member):
        saves["n"] += 1
        if saves["n"] == 1:
            raise ValueError("member is not writable")

    api.members.save.side_effect = fail_first

    response = await api.http.post(
        "/members/import/commit",
        json={
            "rows": [
                commit_row(2),
                commit_row(3, employer_member_id="HR-2", display_label="Bosco"),
            ]
        },
    )

    assert response.status_code == 200, response.text
    results = response.json()["results"]
    assert results[0]["state"] == "failed"
    assert results[0]["message"] == "member is not writable"
    assert results[1]["state"] == "imported"
    assert api.db.rollback.await_count == 1
    assert api.db.commit.await_count == 1


async def test_import_commit_never_overwrites_an_existing_member(api):
    api.clients.get_by_code.return_value = SimpleNamespace(
        id=ClientId("c1"), name="Acme", tenant_id=TenantId("t1")
    )
    api.members.find_by_employer_member_id.return_value = member()

    response = await api.http.post("/members/import/commit", json={"rows": [commit_row()]})

    assert response.status_code == 200, response.text
    assert response.json()["results"][0]["state"] == "duplicate"
    api.db.commit.assert_not_awaited()


async def test_import_commit_rejects_a_company_code_outside_the_tenant(api):
    api.clients.get_by_code.return_value = None

    response = await api.http.post("/members/import/commit", json={"rows": [commit_row()]})

    assert response.status_code == 200, response.text
    result = response.json()["results"][0]
    assert result["state"] == "invalid"
    assert "does not resolve" in result["message"]
    api.db.commit.assert_not_awaited()


async def test_member_import_template_is_server_generated(api):
    response = await api.http.get("/members/import/template")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.splitlines()[0] == (
        "Company Code,Staff_ID,Staff Number,Name of Employee,Email Address,Personal Email,"
        "Date of Birth,Gender,Phone,National ID,Passport Number,Status,Relation,Primary Staff ID"
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
        NextOfKinRelationship.SPOUSE,
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
        NextOfKinRelationship.SPOUSE,
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
