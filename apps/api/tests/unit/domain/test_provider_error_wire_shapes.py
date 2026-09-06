"""Every error body the provider module produces, pinned as serialised.

`to_api_response` maps each details KEY to a field name and its VALUE to that
field's message. A key that is not a form field, or a value that is not a
sentence, produces a detail no client can attach and no person can read. That
happened twice here: `ValidationException` named every field "field", and the
eligibility failure had to override the serialiser to say anything useful.

Pinning the wire shape rather than the exception's attributes is what makes a
third visible. The attributes were correct both times; the serialisation was
not, which is exactly what an attribute test cannot see.

The guard is agent 2's, adopted for these errors.
"""

import re

import pytest

from app.domain.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationException,
)
from app.domain.services.provider_eligibility import (
    EligibilityReason,
    ProviderNotEligibleError,
)

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")

# Details whose message is an identifier rather than prose, deliberately.
#
# provider_id names the subject of an eligibility refusal so a client can tell
# which practitioner was refused. resource_type and resource_id are NotFoundError's
# diagnostic context rather than form fields at all: the serialiser presents
# every details entry as a field error, so they arrive looking like one. That
# is shared behaviour across every 404 in the app and is not repaired here.
_IDENTIFIER_FIELDS = {
    "provider_id",
    "user_id",
    "provider_affiliation_id",
    "resource_id",
    "resource_type",
}


def _is_prose(message: str) -> bool:
    """Whether a message reads as text a person can act on.

    Not a length rule: "Provider not found" is complete. A token count is the
    wrong test, because "batch b-1" passes one. So is counting letter runs,
    because "sess-1 sess-2" contains two of them. The question is whether a
    token is a word at all, so this counts whole alphabetic tokens.
    """
    stripped = message.strip()
    if not stripped or stripped[0] in "[{(":
        return False
    if _IDENTIFIER.match(stripped):
        return False
    words = [token for token in stripped.split() if token.isalpha() and len(token) > 1]
    return len(words) >= 2


_CLIENT_FIELDS = {
    "provider_id",
    "user_id",
    "display_name",
    "email",
    "phone",
    "region",
    "bio",
    "reason",
    "tier",
    "panel_status",
    "accreditation_status",
    "accreditation_expiry",
    "status",
    "delivery_context",
    "provider_affiliation_id",
    "eligibility",
    "resource_type",
    "resource_id",
}


def _errors() -> list[DomainError | ValidationException]:
    return [
        ProviderNotEligibleError(
            "prov-1",
            (
                EligibilityReason("panel_not_active", "Panel status is Suspended, not Active"),
                EligibilityReason("not_accredited", "Accreditation status is Lapsed"),
            ),
        ),
        ValidationException(
            "A booking must state Direct or Organisation delivery",
            field="delivery_context",
        ),
        ConflictError(
            "That account is already linked to another practitioner",
            details={"user_id": "That account is already linked to another practitioner"},
        ),
        NotFoundError("Provider not found", resource_type="Provider", resource_id="prov-1"),
        DomainError("This change requires a non-blank reason"),
    ]


@pytest.mark.parametrize("error", _errors(), ids=lambda e: e.error_code)
class TestEveryProviderErrorBody:
    def test_details_name_a_field_a_client_can_render(self, error):
        for detail in error.to_api_response().get("details", []):
            assert detail["field"] in _CLIENT_FIELDS, (
                f"{error.error_code} attaches to {detail['field']!r}, "
                "which is not a field a client can render against"
            )

    def test_detail_messages_read_as_prose_except_on_identifier_fields(self, error):
        """A bare id is only acceptable where the field is an id."""
        for detail in error.to_api_response().get("details", []):
            message, field = detail["message"], detail["field"]
            assert message, f"{error.error_code} has an empty detail message"
            if field in _IDENTIFIER_FIELDS:
                assert message.strip()[0:1] not in ("[", "{"), "a repr reached an id field"
                continue
            assert _is_prose(message), (
                f"{error.error_code} puts {message!r} on {field!r}, which is not "
                "something a person can act on"
            )

    def test_the_top_level_message_stands_alone(self, error):
        """A client that ignores details still gets a usable sentence."""
        assert _is_prose(error.to_api_response()["message"])

    def test_the_error_code_is_present(self, error):
        assert error.to_api_response()["error"] == error.error_code


class TestEligibilityFailureShape:
    def test_every_reason_carries_a_code_a_client_can_branch_on(self):
        error = ProviderNotEligibleError(
            "prov-1",
            (EligibilityReason("panel_not_active", "Panel status is Suspended, not Active"),),
        )

        details = error.to_api_response()["details"]

        assert all(detail["code"] for detail in details)
        assert "panel_not_active" in [detail["code"] for detail in details]

    def test_several_reasons_share_the_eligibility_field(self):
        """A details dict cannot express this, which is why field_errors exists."""
        error = ProviderNotEligibleError(
            "prov-1",
            (
                EligibilityReason("panel_not_active", "Panel status is Suspended"),
                EligibilityReason("not_accredited", "Accreditation status is Lapsed"),
            ),
        )

        fields = [detail["field"] for detail in error.to_api_response()["details"]]

        assert fields.count("eligibility") == 2


class TestValidationExceptionShape:
    def test_the_message_is_the_sentence_not_the_field_name(self):
        """It once serialised the field name as the message, against field "field"."""
        error = ValidationException("Delivery context is required", field="delivery_context")

        detail = error.to_api_response()["details"][0]

        assert detail["field"] == "delivery_context"
        assert detail["message"] == "Delivery context is required"


class TestTheProsePredicateDiscriminates:
    """Without these the predicate could be weakened to always return True and
    every other case in this file would still pass. A check nothing exercises
    proves nothing, which is the gap that let the original defect through."""

    @pytest.mark.parametrize(
        "message",
        [
            "prov-1",
            "delivery_context",
            "['sess-1', 'sess-2']",
            "{'batch_id': 'b-1'}",
            "batch b-1",
            "sess-1 sess-2",
            "org o-9",
            "",
            "   ",
            "Suspended",
        ],
        ids=[
            "bare-cuid",
            "field-name",
            "list-repr",
            "dict-repr",
            "label-plus-id",
            "two-bare-ids",
            "label-plus-short-id",
            "empty",
            "whitespace",
            "single-word",
        ],
    )
    def test_it_rejects_what_actually_reached_a_message_field(self, message):
        assert _is_prose(message) is False

    @pytest.mark.parametrize(
        "message",
        [
            "Provider not found",
            "Panel status is Suspended, not Active",
            "This change requires a non-blank reason",
            "2 completed session(s) are attributed to this affiliation beyond the new end date",
            "Accreditation expired on 2026-01-01.",
        ],
        ids=["short", "with-comma", "plain", "leading-digit", "trailing-date"],
    )
    def test_it_accepts_a_message_a_person_can_act_on(self, message):
        assert _is_prose(message) is True
