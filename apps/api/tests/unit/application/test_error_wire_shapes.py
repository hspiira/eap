"""Every error body this module produces, pinned as serialised.

to_api_response maps each details KEY to a field name and its VALUE to that
field's message. Passing a key that is not a form field, or a value that is not
a sentence, produces a detail no client can attach and no person can read. That
happened three times here: once found by agent 3 driving the API, twice more by
auditing after their report. Pinning the wire shape rather than the exception's
attributes is what makes a fourth visible.
"""

import re
from datetime import UTC, date, datetime

import pytest

from app.application.use_cases.apply_session_import import ImportRowNotConvertible
from app.application.use_cases.provider_network_use_cases import (
    AffiliationAttributionConflictError,
    AffiliationOverlapError,
)
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.exceptions import DomainError, NotFoundError
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


_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")

# NotFoundError puts these in details, so every 404 in the app carries two
# entries that look like field errors and are really diagnostic context. Same
# category confusion as the defects fixed here, but it predates this migration,
# it is shared by every not-found response, and repairing it changes all of
# them. Exempted visibly rather than silently, and referred to review.
# batch_id joins them for the same reason: IMPORT_ALREADY_STAGED needs the
# conflicting batch's id so a client can offer to resume or discard it, and
# a cuid cannot itself read as a sentence.
_DIAGNOSTIC_FIELDS = {"resource_type", "resource_id", "batch_id"}


def _is_prose(message: str) -> bool:
    """Whether a message reads as text a person can act on.

    Rejects what actually reached message fields here: a bare identifier, a
    Python list or dict repr, and a label paired with an id. Deliberately not a
    length rule, since "Provider not found" is complete.

    The last check counts whole alphabetic tokens rather than tokens or letter
    runs. A token count passes "batch b-1", and counting letter runs passes
    "sess-1 sess-2", because both find two word-like pieces in what is really a
    label and an identifier.
    """
    stripped = message.strip()
    if not stripped or stripped[0] in "[{(":
        return False
    if _IDENTIFIER.match(stripped):
        return False
    words = [token for token in stripped.split() if token.isalpha() and len(token) > 1]
    return len(words) >= 2


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
        NotFoundError(
            "Provider organisation not found",
            resource_type="ProviderOrganisation",
            resource_id="org-1",
        ),
        DomainError(
            "This file was already staged as batch b-1",
            error_code="IMPORT_ALREADY_STAGED",
            http_status=409,
            details={"file": "This file was already staged as batch b-1", "batch_id": "b-1"},
        ),
    ]


@pytest.mark.parametrize("error", _errors(), ids=lambda e: e.error_code)
class TestEveryErrorBody:
    def test_details_name_a_real_form_field(self, error):
        for detail in error.to_api_response().get("details", []):
            if detail["field"] in _DIAGNOSTIC_FIELDS:
                continue
            assert detail["field"] in _FORM_FIELDS, (
                f"{error.error_code} attaches to {detail['field']!r}, "
                "which is not a field a client can render against"
            )

    def test_detail_messages_read_as_sentences(self, error):
        """Not a bare id, and not a Python repr."""
        for detail in error.to_api_response().get("details", []):
            if detail["field"] in _DIAGNOSTIC_FIELDS:
                continue
            assert _is_prose(detail["message"]), (
                f"{error.error_code} detail message is not prose: {detail['message']!r}"
            )

    def test_the_top_level_message_stands_alone(self, error):
        """A client that ignores details still gets a usable sentence.

        Checks that the message is prose, not that it is long. A word count
        rejects "Provider not found", which is complete and usable; the defect
        being guarded against is a bare id or a repr reaching a message field.
        """
        assert _is_prose(error.to_api_response()["message"])

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


class TestTheProseCheckDiscriminates:
    """The guard is only worth having if it rejects what actually went wrong.

    Each rejected case below is a message shape that reached a real response
    body in this module before the fixes: a bare cuid, a list repr, and a field
    name used as a message.
    """

    @pytest.mark.parametrize(
        "message",
        [
            "b-1",
            "m14ugxdtikwlm7ole6oiyihy",
            "valid_from",
            "['sess-1', 'sess-2']",
            "{'field': 'valid_from'}",
            "",
            "   ",
            # A label paired with an id. Agent 1 found the first of these
            # surviving a token count; the second survives counting letter runs.
            "batch b-1",
            "org o-9",
            "sess-1 sess-2",
        ],
    )
    def test_it_rejects_what_is_not_prose(self, message):
        assert _is_prose(message) is False

    @pytest.mark.parametrize(
        "message",
        [
            "Provider not found",
            "Import batch not found",
            "Overlaps affiliation aff-1 (2026-01-01 to 2026-07-01)",
            "2 completed session(s) are attributed to this affiliation",
            "This file was already staged as batch b-1",
        ],
    )
    def test_it_accepts_usable_messages_including_short_ones(self, message):
        """A word count would have rejected the first two."""
        assert _is_prose(message) is True
