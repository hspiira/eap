"""Unit tests for the extracted client import pipeline."""

from app.application.services import client_import
from app.shared.utils.client_csv import ClientCsvRow


def _row(row_number: int, name: str, **overrides) -> ClientCsvRow:
    values = {
        "row_number": row_number,
        "name": name,
        "code": None,
        "phone": None,
        "email": None,
        "address": None,
        "billing_street": None,
        "billing_city": None,
        "billing_country": None,
        "billing_postal_code": None,
        "industry": None,
        "industry_id": None,
        "parent_client_name": None,
        "parent_client_id": None,
        "preferred_contact_method": None,
        "aliases": (),
    }
    values.update(overrides)
    return ClientCsvRow(**values)


class TestPrepareRows:
    def test_generates_a_code_when_the_row_omits_one(self):
        issues: list = []
        candidates, skipped = client_import.prepare_rows([_row(1, "Acme Corp")], issues)
        assert skipped == 0
        assert issues == []
        assert len(candidates) == 1
        row, code = candidates[0]
        assert row.name == "Acme Corp"
        assert 3 <= len(code) <= 5 and code.isalnum()

    def test_duplicate_name_is_skipped_and_its_aliases_are_folded_in(self):
        issues: list = []
        rows = [
            _row(1, "Acme", aliases=("Acme Ltd",)),
            _row(2, "acme", aliases=("Acme Group",)),
        ]
        candidates, skipped = client_import.prepare_rows(rows, issues)
        assert skipped == 1
        assert len(candidates) == 1
        kept, _code = candidates[0]
        assert kept.aliases == ("Acme Ltd", "Acme Group")
        assert issues[0]["severity"] == "skipped"

    def test_rejects_an_invalid_contact_method(self):
        issues: list = []
        candidates, _ = client_import.prepare_rows(
            [_row(1, "Acme", preferred_contact_method="carrier-pigeon")], issues
        )
        assert candidates == []
        assert issues[0]["field"] == "preferred_contact_method"

    def test_rejects_a_malformed_code(self):
        issues: list = []
        candidates, _ = client_import.prepare_rows([_row(1, "Acme", code="AB")], issues)
        assert candidates == []
        assert issues[0]["field"] == "code"

    def test_rejects_a_duplicate_code_within_the_file(self):
        issues: list = []
        rows = [_row(1, "Acme", code="ACME"), _row(2, "Other", code="acme")]
        candidates, _ = client_import.prepare_rows(rows, issues)
        assert len(candidates) == 1
        assert "Duplicate code" in issues[0]["message"]

    def test_generated_codes_stay_unique_across_similar_names(self):
        issues: list = []
        rows = [_row(1, "Acme Corp"), _row(2, "Acme Company"), _row(3, "Acme Consulting")]
        candidates, _ = client_import.prepare_rows(rows, issues)
        assert issues == []
        codes = [code for _row_, code in candidates]
        assert len(codes) == 3
        assert len(set(codes)) == 3


class TestValidateFileAliases:
    def test_flags_an_alias_matching_another_rows_name(self):
        issues: list = []
        candidates = [
            (_row(1, "Acme", aliases=("Globex",)), "ACME"),
            (_row(2, "Globex"), "GLOB"),
        ]
        client_import.validate_file_aliases(candidates, issues)
        assert any("canonical name" in issue["message"] for issue in issues)

    def test_flags_an_alias_repeated_across_rows(self):
        issues: list = []
        candidates = [
            (_row(1, "Acme", aliases=("Shared",)), "ACME"),
            (_row(2, "Other", aliases=("shared",)), "OTHR"),
        ]
        client_import.validate_file_aliases(candidates, issues)
        assert any("repeated" in issue["message"] for issue in issues)

    def test_accepts_distinct_aliases(self):
        issues: list = []
        candidates = [
            (_row(1, "Acme", aliases=("Acme Ltd",)), "ACME"),
            (_row(2, "Globex", aliases=("Globex Inc",)), "GLOB"),
        ]
        client_import.validate_file_aliases(candidates, issues)
        assert issues == []


class TestParseDecisions:
    def test_returns_none_without_a_payload(self):
        assert client_import.parse_decisions("", []) is None

    def test_parses_row_actions(self):
        issues: list = []
        decisions = client_import.parse_decisions(
            '{"3": {"action": "merge", "client_id": "abc"}}', issues
        )
        assert decisions == {3: {"action": "merge", "client_id": "abc"}}
        assert issues == []

    def test_reports_malformed_json(self):
        issues: list = []
        assert client_import.parse_decisions("{not json", issues) == {}
        assert issues[0]["field"] == "decisions"

    def test_rejects_an_unknown_action(self):
        issues: list = []
        decisions = client_import.parse_decisions('{"1": {"action": "destroy"}}', issues)
        assert decisions == {}
        assert "create, skip, or merge" in issues[0]["message"]


class TestValidationResult:
    def test_errors_exclude_warnings_and_skips(self):
        result = client_import.ValidationResult(
            issues=[
                {"row": 1, "field": "name", "message": "bad", "severity": "error"},
                {"row": 2, "field": "name", "message": "close", "severity": "warning"},
                {"row": 3, "field": "name", "message": "dupe", "severity": "skipped"},
            ]
        )
        assert len(result.errors) == 1

    def test_an_issue_without_a_severity_counts_as_an_error(self):
        result = client_import.ValidationResult(
            issues=[{"row": 1, "field": "name", "message": "bad"}]
        )
        assert len(result.errors) == 1


class TestBillingAddress:
    def test_returns_none_without_a_street(self):
        assert client_import.billing_address(_row(1, "Acme")) is None

    def test_builds_an_address_from_the_row(self):
        address = client_import.billing_address(
            _row(
                1,
                "Acme",
                billing_street="1 High St",
                billing_city="Leeds",
                billing_country="UK",
            )
        )
        assert address is not None
        assert address.street == "1 High St"
        assert address.city == "Leeds"
        assert address.country == "UK"

    def test_an_incomplete_billing_address_is_a_row_issue_not_an_exception(self):
        issues: list = []
        candidates, _ = client_import.prepare_rows(
            [_row(1, "Acme", billing_street="1 High St")], issues
        )
        assert candidates == []
        assert issues[0]["field"] == "billing_street"
        assert "city and country" in issues[0]["message"]
