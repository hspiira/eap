"""The member code sequence is read once per client, not once per row."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.services.member_import import MemberCodeIssuer, issue_member_code
from app.domain.value_objects.core import ClientId, TenantId

TENANT = TenantId("t-1")
ACME = ClientId("cli-1")
OTHER = ClientId("cli-2")


def _members(*, sequence=1, taken=()):
    repo = AsyncMock()
    repo.next_member_sequence.return_value = sequence
    taken_codes = set(taken)
    repo.find_by_employer_member_id.side_effect = lambda _t, _c, code: (
        SimpleNamespace(id=code) if code in taken_codes else None
    )
    return repo


class TestSequenceIsReadOncePerClient:
    async def test_a_run_of_enrolments_reads_the_sequence_once(self):
        repo = _members(sequence=1)
        issuer = MemberCodeIssuer(repo)

        codes = [
            await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")
            for _ in range(50)
        ]

        assert codes[0] == "ACME-001"
        assert codes[-1] == "ACME-050"
        assert len(set(codes)) == 50
        repo.next_member_sequence.assert_awaited_once()

    async def test_each_client_keeps_its_own_sequence(self):
        repo = _members(sequence=7)
        issuer = MemberCodeIssuer(repo)

        first = await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")
        other = await issuer.issue(tenant_id=TENANT, client_id=OTHER, client_code="BETA")
        second = await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")

        assert (first, other, second) == ("ACME-007", "BETA-007", "ACME-008")
        assert repo.next_member_sequence.await_count == 2

    async def test_the_first_code_still_skips_one_already_taken(self):
        """A roster imported with hand-written codes continues past them."""
        repo = _members(sequence=1, taken={"ACME-001", "ACME-002"})
        issuer = MemberCodeIssuer(repo)

        first = await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")
        second = await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")

        assert (first, second) == ("ACME-003", "ACME-004")

    async def test_codes_issued_in_the_same_run_are_not_probed_again(self):
        """The run knows what it has issued; only the starting point is read."""
        repo = _members(sequence=1)
        issuer = MemberCodeIssuer(repo)

        for _ in range(10):
            await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")

        assert repo.find_by_employer_member_id.await_count == 1

    async def test_a_prefix_is_normalised_before_it_is_cached(self):
        repo = _members(sequence=3)
        issuer = MemberCodeIssuer(repo)

        first = await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code=" acme ")
        second = await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")

        assert (first, second) == ("ACME-003", "ACME-004")
        repo.next_member_sequence.assert_awaited_once()

    async def test_a_client_with_no_room_left_refuses_rather_than_colliding(self):
        repo = _members(sequence=1, taken={f"ACME-{n:03d}" for n in range(1, 60)})
        issuer = MemberCodeIssuer(repo)

        with pytest.raises(ValueError):
            await issuer.issue(tenant_id=TENANT, client_id=ACME, client_code="ACME")


class TestSingleIssue:
    async def test_the_one_shot_helper_still_issues_a_code(self):
        repo = _members(sequence=2)

        code = await issue_member_code(repo, tenant_id=TENANT, client_id=ACME, client_code="ACME")

        assert code == "ACME-002"
