"""Add presenting_problems and case_referral_sources tables

Revision ID: 3969757e8cd0
Revises: 3ca112aa6972
Create Date: 2026-09-08

Replaces the ``PresentingProblem`` and ``CaseReferralSource`` enums. The
former carried an explicit ``OTHER`` member, already evidence the fixed list
was insufficient. Mirrors ``service_categories`` (migration 7af2412c8b90):
real tables, seeded with the values in use, so a new presenting problem or
referral source is a row an operator adds through the API rather than a code
deploy.

Neither column carried a CHECK constraint (``EnumValueType`` enforced it in
Python only), so this only needs to add the foreign keys, not drop one.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "3969757e8cd0"
down_revision: Union[str, Sequence[str], None] = "3ca112aa6972"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (id, code, name)
_PRESENTING_PROBLEMS: list[tuple[str, str, str]] = [
    ("pp_mental_health", "MentalHealth", "Mental Health"),
    ("pp_stress", "Stress", "Stress"),
    ("pp_relationship", "Relationship", "Relationship"),
    ("pp_work", "Work", "Work"),
    ("pp_financial", "Financial", "Financial"),
    ("pp_substance", "Substance", "Substance"),
    ("pp_bereavement", "Bereavement", "Bereavement"),
    ("pp_trauma", "Trauma", "Trauma"),
    ("pp_family_child", "FamilyChild", "Family/Child"),
    ("pp_other", "Other", "Other"),
]

_REFERRAL_SOURCES: list[tuple[str, str, str]] = [
    ("crs_self", "Self", "Self"),
    ("crs_informal_manager", "InformalManager", "Informal Manager"),
    ("crs_formal_mandatory", "FormalMandatory", "Formal Mandatory"),
    ("crs_hr", "HR", "HR"),
    ("crs_cism_followup", "CISMFollowUp", "CISM Follow-Up"),
    ("crs_employer_proactive", "EmployerProactive", "Employer Proactive"),
]

_FK_PRESENTING_PROBLEM = "fk_cases_presenting_problem_presenting_problems"
_FK_REFERRAL_SOURCE = "fk_cases_referral_source_case_referral_sources"


def _taxonomy_table(name: str):
    return op.create_table(
        name,
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def _seed(table, rows: list[tuple[str, str, str]]) -> None:
    op.bulk_insert(
        table,
        [
            {
                "id": row_id,
                "code": code,
                "name": name,
                "description": None,
                "sort_order": order,
                "is_active": True,
                "version": 1,
                "effective_until": None,
            }
            for order, (row_id, code, name) in enumerate(rows)
        ],
    )


def upgrade() -> None:
    presenting_problems = _taxonomy_table("presenting_problems")
    case_referral_sources = _taxonomy_table("case_referral_sources")

    _seed(presenting_problems, _PRESENTING_PROBLEMS)
    _seed(case_referral_sources, _REFERRAL_SOURCES)

    op.create_foreign_key(
        _FK_PRESENTING_PROBLEM, "cases", "presenting_problems", ["presenting_problem"], ["code"]
    )
    op.create_foreign_key(
        _FK_REFERRAL_SOURCE, "cases", "case_referral_sources", ["referral_source"], ["code"]
    )


def downgrade() -> None:
    op.drop_constraint(_FK_REFERRAL_SOURCE, "cases", type_="foreignkey")
    op.drop_constraint(_FK_PRESENTING_PROBLEM, "cases", type_="foreignkey")
    op.drop_table("case_referral_sources")
    op.drop_table("presenting_problems")
