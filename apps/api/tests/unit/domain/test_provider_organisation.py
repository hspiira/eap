"""Organisation state and approval are independent facts (decision 7)."""

import pytest

from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import ProviderOrganisationId
from app.shared.utils.datetime import utc_now

ACTOR = UserId("u-1")


def _organisation(**overrides) -> ProviderOrganisationEntity:
    now = utc_now()
    defaults = {
        "id": ProviderOrganisationId("org-1"),
        "tenant_id": TenantId("t-1"),
        "name": "Kampala Counselling Partners",
        "created_at": now,
        "updated_at": now,
    }
    return ProviderOrganisationEntity(**{**defaults, **overrides})


class TestDeliveryEligibility:
    def test_a_new_organisation_cannot_deliver(self):
        """Created organisations start Pending, so approval is a deliberate act."""
        assert _organisation().can_deliver() is False

    def test_approved_and_active_can_deliver(self):
        org = _organisation()
        org.change_approval(OrganisationApprovalStatus.APPROVED, ACTOR, "Vetted")
        assert org.can_deliver() is True

    def test_approved_but_deactivated_cannot_deliver(self):
        org = _organisation()
        org.change_approval(OrganisationApprovalStatus.APPROVED, ACTOR, "Vetted")
        org.deactivate(ACTOR, "Left the panel")
        assert org.can_deliver() is False

    def test_active_but_suspended_cannot_deliver(self):
        org = _organisation()
        org.change_approval(OrganisationApprovalStatus.APPROVED, ACTOR, "Vetted")
        org.change_approval(OrganisationApprovalStatus.SUSPENDED, ACTOR, "Under review")
        assert org.can_deliver() is False

    def test_the_two_reasons_stay_distinguishable(self):
        """Eligibility needs to tell a suspended supplier from a retired record."""
        suspended = _organisation(approval_status=OrganisationApprovalStatus.SUSPENDED)
        retired = _organisation(
            approval_status=OrganisationApprovalStatus.APPROVED, is_active=False
        )
        assert (suspended.is_active, suspended.approval_status) == (
            True,
            OrganisationApprovalStatus.SUSPENDED,
        )
        assert (retired.is_active, retired.approval_status) == (
            False,
            OrganisationApprovalStatus.APPROVED,
        )


class TestReasonsAndEvents:
    def test_approval_change_requires_a_reason(self):
        with pytest.raises(DomainError):
            _organisation().change_approval(OrganisationApprovalStatus.APPROVED, ACTOR, " ")

    def test_deactivate_requires_a_reason(self):
        with pytest.raises(DomainError):
            _organisation().deactivate(ACTOR, "")

    def test_approval_change_emits_both_states(self):
        org = _organisation()
        org.change_approval(OrganisationApprovalStatus.APPROVED, ACTOR, "Vetted")
        event = org.events[0]
        assert (event.old_status, event.new_status) == ("Pending", "Approved")
        assert event.reason == "Vetted"

    def test_repeating_an_unchanged_approval_emits_nothing(self):
        org = _organisation(approval_status=OrganisationApprovalStatus.APPROVED)
        org.change_approval(OrganisationApprovalStatus.APPROVED, ACTOR, "Again")
        assert org.events == []

    def test_repeating_deactivation_emits_nothing(self):
        org = _organisation(is_active=False)
        org.deactivate(ACTOR, "Again")
        assert org.events == []

    def test_deactivation_does_not_clear_approval(self):
        """Decision 2 keeps referenced history; deactivation is not a reset."""
        org = _organisation(approval_status=OrganisationApprovalStatus.APPROVED)
        org.deactivate(ACTOR, "Left the panel")
        assert org.approval_status is OrganisationApprovalStatus.APPROVED


class TestInvariants:
    def test_a_blank_name_is_rejected(self):
        with pytest.raises(DomainError):
            _organisation(name="   ")
