"""
PII masking in the Azure SSO callback logs.

The callback logs on every sign-in, so an unmasked address writes identifiable
PII into log storage as routine traffic. Masking keeps the field useful for
correlating a failed login to a tenant/domain without retaining the identity.
"""

import pytest

from app.api.routes.auth_azure import _mask_email


class TestMaskEmail:
    def test_keeps_domain_and_first_initial(self):
        assert _mask_email("fred.hasibiri@minet.co.ug") == "f***@minet.co.ug"

    def test_masks_regardless_of_local_part_length(self):
        """Output must not leak the local part's length."""
        assert _mask_email("a@corp.com") == "a***@corp.com"
        assert _mask_email("averylongaddress@corp.com") == "a***@corp.com"

    def test_handles_subdomains(self):
        assert _mask_email("fred@mail.corp.co.uk") == "f***@mail.corp.co.uk"

    @pytest.mark.parametrize("bad", [None, "", "not-an-email"])
    def test_degrades_safely_on_unusable_input(self, bad):
        """Claims can be absent or malformed; masking must never raise."""
        assert _mask_email(bad) == "<none>"
