"""A re-uploaded roster updating members it already created, end to end.

Every other test of this feature mocks the repositories. These drive the real
routes against a real PostgreSQL, so they are what actually shows that
`update_roster_details` and the audit diff behave against persisted state,
and that a blank cell leaves a stored value alone once that value has been
through the database rather than a mock.
"""

from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.outbox_model import OutboxEventModel

HEADERS = "Company Code,Staff_ID,Name of Employee,Phone,Email Address,Job Title,Department,Status"


def roster(*rows: str) -> dict[str, Any]:
    body = "\n".join([HEADERS, *rows]) + "\n"
    return {"file": ("roster.csv", body.encode(), "text/csv")}


@pytest_asyncio.fixture
async def roster_client(client: AsyncClient) -> dict[str, Any]:
    """An active client with the code the rosters below name."""
    tenant = await client.post(
        "/tenants/",
        json={
            "name": "Roster Update Tenant",
            "code": "roster-update",
            "subscription_tier": "Professional",
            "settings": {
                "max_users": 50,
                "max_clients": 25,
                "features_enabled": ["clients"],
                "custom_branding": False,
            },
        },
    )
    assert tenant.status_code == 201, tenant.text
    created = await client.post(
        f"/clients/?tenant_id={tenant.json()['id']}",
        json={
            "name": "Acme Corporation",
            "code": "ACME",
            "contact_info": {"phone": "+256-700-000000", "email": "hr@acme.test"},
        },
    )
    assert created.status_code == 201, created.text
    return created.json()


async def stage_and_apply(client: AsyncClient, files: dict[str, Any]) -> dict[str, Any]:
    """Stage a roster and apply it without touching any row's decision."""
    staged = await client.post("/members/import", files=files)
    assert staged.status_code == 201, staged.text
    batch_id = staged.json()["id"]
    applied = await client.post(f"/members/import/{batch_id}/apply")
    assert applied.status_code == 200, applied.text
    return {"batch_id": batch_id, "result": applied.json()}


async def rows_of(client: AsyncClient, batch_id: str) -> list[dict[str, Any]]:
    listed = await client.get(f"/members/import/{batch_id}/rows")
    assert listed.status_code == 200, listed.text
    return listed.json()["items"]


async def stored(session: AsyncSession, import_source_id: str) -> EligibleMemberModel:
    session.expire_all()
    found = await session.scalar(
        select(EligibleMemberModel).where(EligibleMemberModel.import_source_id == import_source_id)
    )
    assert found is not None, f"no member stored for {import_source_id}"
    return found


@pytest_asyncio.fixture
async def enrolled(client: AsyncClient, roster_client: dict) -> dict[str, Any]:
    """One member, created by an ordinary first import of the roster."""
    first = await stage_and_apply(
        client,
        roster(
            "ACME,HR-1,Amina Namukasa,0700111222,amina@acme.com,Teller,Operations,Active",
        ),
    )
    assert first["result"]["imported"] == 1, first["result"]
    return first


class TestUpdatingAMemberARosterAlreadyCreated:
    async def test_a_second_roster_matches_the_member_and_offers_an_update(
        self, client: AsyncClient, enrolled: dict
    ):
        staged = await client.post(
            "/members/import",
            files=roster("ACME,HR-1,Amina Namukasa,0700999888,,Branch Manager,,Active"),
        )
        assert staged.status_code == 201, staged.text

        rows = await rows_of(client, staged.json()["id"])
        assert len(rows) == 1
        assert rows[0]["outcome"] == "Duplicate"
        assert rows[0]["matched_member_id"] is not None
        # Never Update by default: a batch nobody reviews touches nobody.
        assert rows[0]["decision"] == "skip"

    async def test_applying_without_choosing_update_leaves_the_member_untouched(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        applied = await stage_and_apply(
            client,
            roster("ACME,HR-1,Amina Namukasa,0700999888,,Branch Manager,,Active"),
        )

        assert applied["result"]["updated"] == 0
        assert applied["result"]["imported"] == 0
        member = await stored(db_session, "HR-1")
        assert member.phone == "0700111222"
        assert member.job_title == "Teller"

    async def test_choosing_update_writes_the_roster_values_onto_the_member(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        staged = await client.post(
            "/members/import",
            files=roster("ACME,HR-1,Amina Namukasa,0700999888,,Branch Manager,,Active"),
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]

        decided = await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )
        assert decided.status_code == 200, decided.text

        applied = await client.post(f"/members/import/{batch_id}/apply")
        assert applied.status_code == 200, applied.text
        assert applied.json()["updated"] == 1
        assert applied.json()["imported"] == 0

        member = await stored(db_session, "HR-1")
        assert member.phone == "0700999888"
        assert member.job_title == "Branch Manager"

    async def test_a_blank_cell_does_not_clear_what_the_member_already_has(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        """The decision this feature turns on, proved against stored state.

        The second roster leaves Email Address and Department blank. Neither
        may be cleared: an import adds and corrects, it never empties.
        """
        before = await stored(db_session, "HR-1")
        assert before.work_email == "amina@acme.com"
        assert before.department == "Operations"

        staged = await client.post(
            "/members/import",
            files=roster("ACME,HR-1,Amina Namukasa,0700999888,,Branch Manager,,Active"),
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]
        await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )
        applied = await client.post(f"/members/import/{batch_id}/apply")
        assert applied.json()["updated"] == 1

        member = await stored(db_session, "HR-1")
        assert member.work_email == "amina@acme.com"
        assert member.department == "Operations"
        assert member.phone == "0700999888"

    async def test_identity_survives_an_update(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        """The member code is server-issued once and an update never reissues it."""
        code_before = (await stored(db_session, "HR-1")).employer_member_id

        staged = await client.post(
            "/members/import",
            files=roster("ACME,HR-1,Amina Nakato,0700999888,,,,Active"),
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]
        await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )
        await client.post(f"/members/import/{batch_id}/apply")

        member = await stored(db_session, "HR-1")
        assert member.employer_member_id == code_before
        assert member.import_source_id == "HR-1"
        assert member.display_label == "Amina Nakato"

    async def test_a_roster_that_changes_nothing_is_reported_as_unchanged(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        staged = await client.post(
            "/members/import",
            files=roster(
                "ACME,HR-1,Amina Namukasa,0700111222,amina@acme.com,Teller,Operations,Active"
            ),
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]
        await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )

        applied = await client.post(f"/members/import/{batch_id}/apply")
        assert applied.status_code == 200, applied.text
        assert applied.json()["unchanged"] == 1
        assert applied.json()["updated"] == 0

    async def test_the_roster_status_moves_the_member(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        staged = await client.post(
            "/members/import",
            files=roster("ACME,HR-1,Amina Namukasa,,,,,Terminated"),
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]
        await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )
        applied = await client.post(f"/members/import/{batch_id}/apply")
        assert applied.json()["updated"] == 1

        assert (await stored(db_session, "HR-1")).status == "Terminated"

    async def test_an_update_is_audited_naming_only_the_field_that_changed(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        """The audit has to say what changed, not merely that something did.

        Only `phone` is revised here, so only `phone` may appear in the diff
        beside the import timestamp. The values themselves are redacted: a
        member is special-category personal data, and the audit records which
        field moved rather than what it moved to.
        """
        staged = await client.post(
            "/members/import",
            files=roster("ACME,HR-1,Amina Namukasa,0700999888,,,,Active"),
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]
        await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )
        await client.post(f"/members/import/{batch_id}/apply")

        updates = [
            event
            for event in await db_session.scalars(select(OutboxEventModel))
            if event.event_type == "EligibleMemberUpdated"
        ]
        assert len(updates) == 1, [event.event_type for event in updates]
        payload = updates[0].payload
        changed = {change["field_name"] for change in payload["field_changes"]}
        assert changed == {"phone", "last_imported_at"}, changed
        assert payload["is_special_category"] is True
        assert all(
            change["new_value"] == "[redacted]"
            for change in payload["field_changes"]
            if change["field_name"] == "phone"
        )

    async def test_a_row_that_changes_nothing_writes_no_audit_record(
        self, client: AsyncClient, db_session: AsyncSession, enrolled: dict
    ):
        staged = await client.post(
            "/members/import",
            files=roster(
                "ACME,HR-1,Amina Namukasa,0700111222,amina@acme.com,Teller,Operations,Active"
            ),
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]
        await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )
        applied = await client.post(f"/members/import/{batch_id}/apply")
        assert applied.json()["unchanged"] == 1

        updates = [
            event
            for event in await db_session.scalars(select(OutboxEventModel))
            if event.event_type == "EligibleMemberUpdated"
        ]
        assert updates == []


class TestWhatAnUpdateRefuses:
    async def test_a_contradicting_relation_withholds_the_match(
        self, client: AsyncClient, enrolled: dict
    ):
        body = (
            "Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
            "ACME,HR-1,Amina Namukasa,Spouse,HR-9\n"
        )
        staged = await client.post(
            "/members/import", files={"file": ("roster.csv", body.encode(), "text/csv")}
        )
        assert staged.status_code == 201, staged.text

        row = (await rows_of(client, staged.json()["id"]))[0]
        assert row["outcome"] == "Duplicate"
        assert row["matched_member_id"] is None
        assert "Spouse" in (row["message"] or "")

    async def test_a_row_that_matched_nobody_refuses_the_update_decision(
        self, client: AsyncClient, enrolled: dict
    ):
        body = (
            "Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
            "ACME,HR-1,Amina Namukasa,Spouse,HR-9\n"
        )
        staged = await client.post(
            "/members/import", files={"file": ("roster.csv", body.encode(), "text/csv")}
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]

        refused = await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "update"}
        )

        assert refused.status_code == 400, refused.text

    async def test_a_matched_row_refuses_the_import_decision(
        self, client: AsyncClient, enrolled: dict
    ):
        """Update revises that member; it never enrols a second under their Staff_ID."""
        staged = await client.post(
            "/members/import", files=roster("ACME,HR-1,Amina Namukasa,,,,,Active")
        )
        batch_id = staged.json()["id"]
        row = (await rows_of(client, batch_id))[0]

        refused = await client.patch(
            f"/members/import/{batch_id}/rows/{row['id']}", json={"decision": "import"}
        )

        assert refused.status_code == 400, refused.text


class TestRestagingTheSameFile:
    """The tenth defect: a file-scoped replay key held past a write.

    A row with no Staff_ID of its own is keyed `file:{hash}:row:{n}`, and
    staging the same file again recomputes that key exactly. A row still
    holding one after it imported collides with its own successor on
    (tenant_id, replay_key), taking the whole insert down.

    Reaching it needs two files: a dependant sharing a file with their primary
    is Invalid on first staging, because the primary is not a member yet, so
    such a row never imports and never holds a key.
    """

    DEPENDANT = (
        "Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
        "ACME,,Junior Namukasa,Child,HR-1\n"
    )

    async def test_a_file_whose_dependant_imported_can_be_staged_again(
        self, client: AsyncClient, enrolled: dict
    ):
        files = {"file": ("dependants.csv", self.DEPENDANT.encode(), "text/csv")}

        first = await client.post("/members/import", files=files)
        assert first.status_code == 201, first.text
        applied = await client.post(f"/members/import/{first.json()['id']}/apply")
        assert applied.status_code == 200, applied.text
        assert applied.json()["imported"] == 1, applied.json()

        again = await client.post("/members/import", files=files)

        assert again.status_code == 201, again.text

    async def test_a_file_of_ordinary_rows_can_be_staged_again(
        self, client: AsyncClient, enrolled: dict
    ):
        """The counterpart: an identity key is kept, and restaging still works
        because the re-judged row is a Duplicate and takes a different key."""
        files = roster(
            "ACME,HR-1,Amina Namukasa,0700111222,amina@acme.com,Teller,Operations,Active"
        )

        again = await client.post("/members/import", files=files)

        assert again.status_code == 201, again.text
        rows = await rows_of(client, again.json()["id"])
        assert rows[0]["outcome"] == "Duplicate"
