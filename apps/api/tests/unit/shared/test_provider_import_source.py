"""Parsing the extract: it reads columns and never infers identity."""

import pytest

from app.domain.exceptions import DomainError
from app.shared.utils.provider_import_source import parse_source_rows

HEADER = "DATE,COUNSELOR,COUNSELOR (CLEAN),ACTIVITY LOG ID\n"


def _csv(*rows: str) -> bytes:
    return (HEADER + "".join(row + "\n" for row in rows)).encode("utf-8")


class TestColumns:
    def test_the_cleaned_counsellor_column_is_preferred(self):
        rows = parse_source_rows(_csv("2025-04-02,Dr A Nakato,Alice Nakato,LOG-1"), None)
        assert rows[0].raw_practitioner_name == "Alice Nakato"

    def test_row_numbers_are_one_based_over_data_rows(self):
        rows = parse_source_rows(_csv("2025-04-02,A,A,L1", "2025-04-03,B,B,L2"), None)
        assert [r.row_number for r in rows] == [1, 2]

    def test_a_stable_key_column_is_read_when_named(self):
        rows = parse_source_rows(_csv("2025-04-02,A,A,LOG-9"), "ACTIVITY LOG ID")
        assert rows[0].source_record_key == "LOG-9"

    def test_no_key_column_leaves_the_key_absent(self):
        rows = parse_source_rows(_csv("2025-04-02,A,A,LOG-9"), None)
        assert rows[0].source_record_key is None

    def test_an_unknown_key_column_is_rejected(self):
        with pytest.raises(DomainError):
            parse_source_rows(_csv("2025-04-02,A,A,L1"), "NOT A COLUMN")

    def test_a_file_without_a_date_column_is_rejected(self):
        with pytest.raises(DomainError):
            parse_source_rows(b"COUNSELOR\nAlice\n", None)


class TestValues:
    def test_a_blank_name_becomes_none_not_an_empty_string(self):
        """The staging service treats None as missing; '' would look like a name."""
        rows = parse_source_rows(_csv("2025-04-02,,,L1"), None)
        assert rows[0].raw_practitioner_name is None

    def test_an_unparseable_date_becomes_none(self):
        """Left for the staging service to reject with a reason."""
        rows = parse_source_rows(_csv("not a date,A,A,L1"), None)
        assert rows[0].session_date is None

    @pytest.mark.parametrize(
        "raw,expected_day", [("2025-04-02", 2), ("02/04/2025", 2), ("02-Apr-2025", 2)]
    )
    def test_common_date_formats_parse(self, raw, expected_day):
        rows = parse_source_rows(_csv(f"{raw},A,A,L1"), None)
        assert rows[0].session_date is not None
        assert rows[0].session_date.day == expected_day

    def test_no_delivery_context_is_inferred_by_the_parser(self):
        rows = parse_source_rows(_csv("2025-04-02,A,A,L1"), None)
        assert rows[0].organisation_affiliation_id is None

    def test_a_byte_order_mark_is_handled(self):
        content = ("﻿" + HEADER + "2025-04-02,A,A,L1\n").encode("utf-8")
        assert parse_source_rows(content, None)[0].session_date is not None

    def test_non_utf8_content_is_rejected(self):
        with pytest.raises(DomainError):
            parse_source_rows(b"\xff\xfe\x00bad", None)
