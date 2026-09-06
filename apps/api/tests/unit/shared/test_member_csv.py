from app.shared.utils.member_csv import parse_member_csv


def test_parser_requires_explicit_stable_staff_id():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Staff Number,Name of Employee\nACME,,12345,Jane Doe\n"
    )
    assert rows[0].employer_member_id is None
    assert any(issue["field"] == "Staff_ID" for issue in issues)


def test_parser_maps_roster_fields_and_rejects_placeholder_ids():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Email Address,Status\n"
        b"ACME,IDI-,Jane Doe,N/A,Active\n"
    )
    assert rows[0].work_email is None
    assert rows[0].display_label == "Jane Doe"
    assert any(issue["row"] == 2 for issue in issues)
