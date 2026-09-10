from datetime import date

import pytest

from app.shared.utils.member_csv import parse_member_csv, parse_roster_date


def test_parse_roster_date_accepts_iso_first():
    assert parse_roster_date("2026-04-03") == date(2026, 4, 3)


def test_parse_roster_date_resolves_day_first():
    """03/04/2026 is 3 April, not March 4: this importer serves a day-first region."""
    assert parse_roster_date("03/04/2026") == date(2026, 4, 3)


def test_parse_roster_date_accepts_dash_separators():
    assert parse_roster_date("03-04-2026") == date(2026, 4, 3)


def test_parse_roster_date_falls_back_to_month_first_when_day_first_is_not_a_real_date():
    """12/25/2026 cannot be day 12 of month 25, so it must be 25 December."""
    assert parse_roster_date("12/25/2026") == date(2026, 12, 25)


def test_parse_roster_date_rejects_nonsense():
    with pytest.raises(ValueError, match="Unrecognised date"):
        parse_roster_date("not a date")


def test_parse_roster_date_rejects_a_two_digit_year():
    with pytest.raises(ValueError, match="Unrecognised date"):
        parse_roster_date("03/04/26")


def test_parser_requires_explicit_stable_staff_id():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Staff Number,Name of Employee\nACME,,12345,Jane Doe\n"
    )
    assert rows[0].import_source_id is None
    assert any(issue["field"] == "Staff_ID" for issue in issues)


def test_a_dependant_does_not_need_their_own_staff_id():
    """A dependant is identified by Primary Staff ID; only the employee needs their own."""
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
        b"ACME,,Jane Doe Jr,Child,AC-1\n"
    )
    assert rows[0].import_source_id is None
    assert not any(issue["field"] == "Staff_ID" for issue in issues)


def test_a_dependant_with_a_dirty_staff_id_is_still_flagged():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Relation,Primary Staff ID\n"
        b"ACME,IDI-,Jane Doe Jr,Child,AC-1\n"
    )
    assert any(issue["field"] == "Staff_ID" for issue in issues)


def test_parser_maps_roster_fields_and_rejects_placeholder_ids():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Email Address,Status\n"
        b"ACME,IDI-,Jane Doe,N/A,Active\n"
    )
    assert rows[0].work_email is None
    assert rows[0].display_label == "Jane Doe"
    assert any(issue["row"] == 2 for issue in issues)


def test_parser_maps_member_profile_fields():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Email Address,Personal Email,Date of Birth,Gender,Phone,National ID,Passport Number\n"
        b"ACME,AC-1,Jane Doe,jane@example.test,jane.personal@example.test,1990-01-31,Female,+256700000000,CM123,B123\n"
    )
    assert issues == []
    assert rows[0].personal_email == "jane.personal@example.test"
    assert rows[0].date_of_birth == "1990-01-31"
    assert rows[0].phone == "+256700000000"
    assert rows[0].national_id == "CM123"
    assert rows[0].passport_number == "B123"


def test_parser_maps_date_joined_and_leaves_it_blank_when_absent():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Date Joined\nACME,AC-1,Jane Doe,03/04/2026\n"
    )
    assert issues == []
    assert rows[0].date_joined == "03/04/2026"

    rows, issues = parse_member_csv(b"Company Code,Staff_ID,Name of Employee\nACME,AC-2,John Doe\n")
    assert issues == []
    assert rows[0].date_joined is None


def test_parser_maps_the_optional_employment_columns():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Job Title,Job Classification,Skill,"
        b"Department,Unit,Contract type\n"
        b"ACME,AC-1,Jane Doe,Branch Manager,Manager,Officer,Operations,"
        b"Kampala Road branch,Permanent\n"
    )
    assert issues == []
    row = rows[0]
    assert row.job_title == "Branch Manager"
    assert row.job_classification == "Manager"
    assert row.skill == "Officer"
    assert row.department == "Operations"
    assert row.unit == "Kampala Road branch"
    assert row.employment_type == "Permanent"


def test_employment_columns_are_optional():
    rows, issues = parse_member_csv(b"Company Code,Staff_ID,Name of Employee\nACME,AC-1,Jane Doe\n")
    assert issues == []
    row = rows[0]
    assert row.job_title is None
    assert row.department is None
    assert row.employment_type is None


def test_excel_error_placeholders_are_read_as_absent():
    """The sample roster carries a literal #N/A in 17 Job Classification cells."""
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Name of Employee,Job Classification,Unit\n"
        b"ACME,AC-1,Jane Doe,#N/A,N/A\n"
    )
    assert issues == []
    assert rows[0].job_classification is None
    assert rows[0].unit is None
