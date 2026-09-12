"""Builds the downloadable session-import workbook.

Dropdown values live on a hidden reference sheet and are wired to their
column with Excel data validation. This is a client-side affordance only: it
does not replace server-side validation, since a paste, a non-Excel editor,
or someone typing over the cell can all still produce a value the dropdown
would have blocked. `provider_import_source.py` validates every row the same
way regardless of how it got there.
"""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

_HEADERS = (
    "Date",
    "Time",
    "Company (CLEAN)",
    "Client Code",
    "Client-ID#",
    "Counselor (CLEAN)",
    "Client Type (Staff/Dep)",
    "Gender",
    "Session Type",
    "Session Category",
    "Client Type",
    "Intervention",
    "Status (CLEAN)",
    "Rate (UGX)",
    "Session #",
    "Issue/Topic",
    "Diagnosis Type",
    "Diagnosis",
    "Approved By",
    "Organisation Session",
)

#: Reference sheet column order. Only headers named here get a dropdown.
_DROPDOWN_HEADERS = (
    "Client Code",
    "Client Type (Staff/Dep)",
    "Gender",
    "Session Type",
    "Session Category",
    "Client Type",
    "Intervention",
    "Status (CLEAN)",
    "Diagnosis Type",
    "Diagnosis",
    "Approved By",
    "Organisation Session",
)

_STATIC_LISTS: dict[str, tuple[str, ...]] = {
    "Client Type (Staff/Dep)": ("Staff", "Group/Event"),
    "Gender": ("Female", "Male", "Group"),
    "Session Type": ("Physical", "Online"),
    "Session Category": ("Individual", "Group", "Family", "Couples"),
    "Client Type": ("New", "Repeat"),
    "Intervention": (
        "Individual Counselling",
        "Health Talk",
        "Family Therapy",
        "Coaching/Mentorship",
        "Physical Wellness",
        "Couple Counselling",
        "Group Counselling",
        "Mental Health Talk",
        "Psychiatric Assessment",
        "Psychotherapy",
        "Empowerment Talk",
    ),
    "Status (CLEAN)": ("Ongoing", "Completed", "Referred", "Terminated", "No Show"),
    #: Blank is not offered: it is what an old row with no evidence looks like,
    #: and staging must not read it as either answer.
    "Organisation Session": ("Yes", "No"),
}

_EXAMPLE_ROWS = (
    (
        "2026-01-15",
        "Example Client",
        "EXM",
        "EXM-001",
        "Example Counsellor",
        "Staff",
        "Female",
        "Physical",
        "Individual",
        "New",
        "Individual Counselling",
        "Completed",
        "50000",
        "1",
        "Work stress",
        "Mental_Ill_Health",
        "Depression",
        "Example Approver",
        "Yes",
    ),
    (
        "2026-01-16",
        "Example Client",
        "EXM",
        "",
        "Example Counsellor",
        "Group/Event",
        "",
        "Physical",
        "Group",
        "",
        "Health Talk",
        "Completed",
        "",
        "",
        "",
        "",
        "",
        "",
        "No",
    ),
)

_DATA_ROWS_RESERVED = 1000


def build_session_import_workbook(
    *,
    client_codes: list[str],
    diagnosis_types: list[str],
    diagnoses: list[str],
    approver_names: list[str],
) -> bytes:
    """One workbook: the "Sessions" sheet to fill in, plus a hidden reference sheet."""
    tenant_lists = {
        "Client Code": tuple(client_codes),
        "Diagnosis Type": tuple(diagnosis_types),
        "Diagnosis": tuple(diagnoses),
        "Approved By": tuple(approver_names),
    }
    lists = {
        name: _STATIC_LISTS.get(name, tenant_lists.get(name, ())) for name in _DROPDOWN_HEADERS
    }

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sessions"
    sheet.append(_HEADERS)
    for row in _EXAMPLE_ROWS:
        sheet.append(row)

    reference = workbook.create_sheet("Reference Lists")
    reference.sheet_state = "hidden"
    _write_reference_lists(reference, lists)
    _add_dropdowns(sheet, lists)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _write_reference_lists(reference: Worksheet, lists: dict[str, tuple[str, ...]]) -> None:
    for column_index, name in enumerate(_DROPDOWN_HEADERS, start=1):
        for row_index, value in enumerate(lists[name] or ("",), start=1):
            reference.cell(row=row_index, column=column_index, value=value)


def _add_dropdowns(sheet: Worksheet, lists: dict[str, tuple[str, ...]]) -> None:
    for reference_column_index, name in enumerate(_DROPDOWN_HEADERS, start=1):
        target_column = get_column_letter(_HEADERS.index(name) + 1)
        reference_column = get_column_letter(reference_column_index)
        row_count = max(len(lists[name]), 1)
        validation = DataValidation(
            type="list",
            formula1=f"'Reference Lists'!${reference_column}$1:${reference_column}${row_count}",
            allow_blank=True,
        )
        sheet.add_data_validation(validation)
        validation.add(f"{target_column}2:{target_column}{_DATA_ROWS_RESERVED}")
