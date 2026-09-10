from app.shared.utils.member_csv import parse_member_csv


def test_parser_requires_explicit_stable_staff_id():
    rows, issues = parse_member_csv(
        b"Company Code,Staff_ID,Staff Number,Name of Employee\nACME,,12345,Jane Doe\n"
    )
    assert rows[0].import_source_id is None
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
