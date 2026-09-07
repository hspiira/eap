"""Build synthetic practitioner workbooks for tests."""

import io

from openpyxl import Workbook

PARTNER_TITLE = "LIST OF MINET EMPLOYEE WELLNESS SERVICE PROVIDERS 2023"

PARTNER_HEADERS = [
    "NO",
    "INDIVIDUAL/COMPANY NAME",
    "NAME (First/Surname)",
    "PROFESSION",
    "AREA OF STRENGTH",
    "CONTACT MOBILE 1",
    "MOBILE CONTACT 2",
    "CONTACT EMAIL",
    "OFFICE LOCATION",
]

CONSULTANT_HEADERS = [
    "NAME",
    "COMPANY",
    "EMAIL",
    "Saluttion",
    "Speciality",
    "Contract",
    "Counsel",
    "Talks",
    "Flexibilibility",
]


def workbook_bytes(partner_rows=(), consultant_rows=()) -> bytes:
    """A workbook shaped like the reference file: title row, then headers."""
    workbook = Workbook()
    partner = workbook.active
    partner.title = "Minet EAP Partner list"
    partner.append([PARTNER_TITLE])
    partner.append(PARTNER_HEADERS)
    for row in partner_rows:
        partner.append(row)
    consultants = workbook.create_sheet("EAP Consultants - General")
    consultants.append(CONSULTANT_HEADERS)
    for row in consultant_rows:
        consultants.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def partner_row(
    name="Jane Doe",
    company="Individual",
    profession="Clinical Psychologist",
    email="jane@example.com",
    *,
    strength="Trauma",
    mobile_1="0700000001",
    mobile_2="0770000001",
    location="Muyenga",
) -> list:
    return [1, company, name, profession, strength, mobile_1, mobile_2, email, location]


def consultant_row(
    name="John Okello",
    company="Individual",
    email="john@example.com",
    speciality="Counselling",
    contract="Done",
    *,
    salutation="Mr. Okello",
    counsel=60000,
    talks=500000,
    flexibility="Flexible",
) -> list:
    return [name, company, email, salutation, speciality, contract, counsel, talks, flexibility]
