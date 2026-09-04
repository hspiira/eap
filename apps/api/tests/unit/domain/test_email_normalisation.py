"""
Email value-object normalisation.

Regression cover for the "account has not been provisioned" class of login
failure: `users.email` is compared with `=` (case-SENSITIVE on PostgreSQL) while
the Azure SSO callback lowercases the incoming UPN claim. A user provisioned as
`Fred.H@corp.com` was therefore unreachable via SSO, with the two addresses
looking identical to whoever was reading the logs.
"""

import pytest

from app.domain.value_objects.core import Email


class TestEmailNormalisation:
    def test_lowercases_local_and_domain(self):
        assert Email("Fred.Hasibiri@Minet.CO.UG").value == "fred.hasibiri@minet.co.ug"

    def test_strips_surrounding_whitespace(self):
        assert Email("  fred@minet.co.ug  ").value == "fred@minet.co.ug"

    def test_case_variants_compare_equal(self):
        """The point of normalising: provisioning and login agree on identity."""
        assert Email("Fred.H@corp.com") == Email("fred.h@corp.com")

    def test_case_variants_hash_equal(self):
        """Frozen dataclass; equal values must be interchangeable as dict/set keys."""
        assert len({Email("Fred@corp.com"), Email("fred@corp.com")}) == 1

    def test_accepts_azure_b2b_guest_upn(self):
        """
        B2B guests arrive as `local_domain.com#EXT#@tenant.onmicrosoft.com`.
        The old regex rejected '#', so these raised ValueError inside the SSO
        callback and surfaced as a 500 blank page.
        """
        guest = Email("fred_gmail.com#EXT#@evexia.onmicrosoft.com")
        assert guest.value == "fred_gmail.com#ext#@evexia.onmicrosoft.com"

    @pytest.mark.parametrize(
        "bad",
        ["", "   ", "not-an-email", "@nodomain.com", "no-at-sign.com", "trailing@dot."],
    )
    def test_rejects_malformed(self, bad):
        with pytest.raises(ValueError):
            Email(bad)

    def test_rejects_over_length(self):
        with pytest.raises(ValueError):
            Email("a" * 250 + "@corp.com")
