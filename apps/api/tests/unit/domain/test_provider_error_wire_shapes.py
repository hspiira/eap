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

    def test_detail_messages_read_as_sentences_or_identifiers(self, error):
        """A message is either prose or a deliberate identifier, never a repr."""
        for detail in error.to_api_response().get("details", []):
            message = detail["message"]
            assert message, f"{error.error_code} has an empty detail message"
            assert not message.startswith("["), "a list repr reached a detail message"
            assert not message.startswith("{"), "a dict repr reached a detail message"

    def test_the_top_level_message_stands_alone(self, error):
        """A client that ignores details still gets a usable sentence.

        Three words, not four: "Provider not found" is complete. The check is
        against a bare id or a single word, not against brevity.
        """
        assert len(error.to_api_response()["message"].split()) >= 3

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
