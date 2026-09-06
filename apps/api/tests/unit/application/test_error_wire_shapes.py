"""Every error body this module produces, pinned as serialised.

to_api_response maps each details KEY to a field name and its VALUE to that
field's message. Passing a key that is not a form field, or a value that is not
a sentence, produces a detail no client can attach and no person can read. That
happened three times here: once found by agent 3 driving the API, twice more by
auditing after their report. Pinning the wire shape rather than the exception's
attributes is what makes a fourth visible.
"""

from datetime import UTC, date, datetime

import pytest

from app.application.use_cases.apply_session_import import ImportRowNotConvertible
from app.application.use_cases.provider_network_use_cases import (
    AffiliationAttributionConflictError,
    AffiliationOverlapError,
)
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)

_FORM_FIELDS = {
    "valid_from",
    "valid_until",
    "provider_id",
    "organisation_id",
    "name",
    "reason",
    "note",
    "file",
    "specialty_id",
}


def _affiliation() -> ProviderAffiliationEntity:
    return ProviderAffiliationEntity(
        id=ProviderAffiliationId("aff-1"),
        tenant_id=TenantId("t-1"),
        provider_id=ProviderId("prov-1"),
        organisation_id=ProviderOrganisationId("org-1"),
        valid_from=date(2026, 1, 1),
        valid_until=date(2026, 7, 1),
        created_at=NOW,
        updated_at=NOW,
    )


def _errors() -> list[DomainError]:
    return [
        AffiliationOverlapError(_affiliation(), "valid_from"),
        AffiliationOverlapError(_affiliation(), "valid_until"),
        AffiliationAttributionConflictError(["sess-1", "sess-2"]),
        ImportRowNotConvertible(4, "no session date"),
        DomainError(
            "This file was already staged as batch b-1",
            error_code="IMPORT_ALREADY_STAGED",
            http_status=409,
            details={"file": "This file was already staged as batch b-1"},
        ),
    ]


@pytest.mark.parametrize("error", _errors(), ids=lambda e: e.error_code)
class TestEveryErrorBody:
    def test_details_name_a_real_form_field(self, error):
        for detail in error.to_api_response().get("details", []):
            assert detail["field"] in _FORM_FIELDS, (
                f"{error.error_code} attaches to {detail['field']!r}, "
                "which is not a field a client can render against"
            )

    def test_detail_messages_read_as_sentences(self, error):
        """Not a bare id, and not a Python repr."""
        for detail in error.to_api_response().get("details", []):
            message = detail["message"]
            assert " " in message, f"{error.error_code} detail message is not a sentence"
            assert not message.startswith("["), "a list repr reached a detail message"
            assert message[0].isupper() or message[0].isdigit()

    def test_the_top_level_message_stands_alone(self, error):
        """A client that ignores details still gets a usable sentence."""
        message = error.to_api_response()["message"]
        assert len(message.split()) >= 4

    def test_the_error_code_is_present(self, error):
        assert error.to_api_response()["error"] == error.error_code


class TestAttributionConflictKeepsTheIds:
    def test_the_offending_sessions_are_named(self):
        """Agent 1 asked for the ids; they live in the sentence, not a repr."""
        body = AffiliationAttributionConflictError(["sess-1", "sess-2"]).to_api_response()
        assert "sess-1" in body["message"]
        assert "sess-2" in body["message"]

    def test_it_attaches_to_the_field_the_caller_changed(self):
        body = AffiliationAttributionConflictError(["sess-1"]).to_api_response()
        assert body["details"][0]["field"] == "valid_until"
