from datetime import date, time

from app.shared.utils.provider_import_source import parse_source_rows
from app.shared.utils.session_import_template import build_session_import_workbook


def _parsed_template_rows():
    workbook = build_session_import_workbook(
        client_codes=["EXM"],
        diagnosis_types=["Mental_Ill_Health"],
        diagnoses=["Depression"],
        approver_names=["Example Approver"],
    )
    return parse_source_rows(workbook, None)


def test_the_individual_example_row_lands_under_its_own_headers() -> None:
    row = _parsed_template_rows()[0]

    assert row.session_date == date(2026, 1, 15)
    assert row.session_time == time(9, 30)
    assert row.raw_client_name == "Example Client"
    assert row.raw_client_code == "EXM"
    assert row.raw_member_ref == "EXM-001"
    assert row.raw_practitioner_name == "Example Counsellor"
    assert row.raw_audience == "Staff"
    assert row.raw_gender == "Female"
    assert row.raw_session_type == "Physical"
    assert row.raw_category == "Individual"
    assert row.raw_client_type == "New"
    assert row.raw_intervention == "Individual Counselling"
    assert row.raw_status == "Completed"
    assert row.raw_rate == "50000"
    assert row.raw_session_number == "1"
    assert row.raw_issue_topic == "Work stress"
    assert row.raw_diagnosis_type == "Mental_Ill_Health"
    assert row.raw_diagnosis == "Depression"
    assert row.raw_approved_by == "Example Approver"
    assert row.raw_organisation_session == "Yes"


def test_the_company_wide_example_row_lands_under_its_own_headers() -> None:
    row = _parsed_template_rows()[1]

    assert row.session_date == date(2026, 1, 16)
    assert row.session_time == time(14, 0)
    assert row.raw_client_name == "Example Client"
    assert row.raw_client_code == "EXM"
    assert row.raw_practitioner_name == "Example Counsellor"
    assert row.raw_audience == "Group/Event"
    assert row.raw_session_type == "Physical"
    assert row.raw_category == "Group"
    assert row.raw_intervention == "Health Talk"
    assert row.raw_status == "Completed"
    assert row.raw_organisation_session == "No"
