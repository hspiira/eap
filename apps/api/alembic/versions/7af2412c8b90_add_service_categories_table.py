"""Add service_categories table, replacing the ServiceCategory enum

Revision ID: 7af2412c8b90
Revises: j5d7f9h1k3m5
Create Date: 2026-09-08

``ServiceCategory`` gated ``services.category`` and
``authorizations.service_category`` from Python, so every new category (most
recently Psychoeducation and Assessment) needed a code deploy and, for
``services``, a migration to widen its CHECK constraint. This mirrors
``diagnosis_types``: a real table, seeded with the categories already in use,
so the next new category is a row an operator adds through the API rather
than a migration.

Seeds all nine categories in use as of this migration: the original seven the
enum carried, plus Psychoeducation and Assessment. ``services.category``'s
CHECK constraint (migration a5b8c1d4e7f0) is dropped in favour of a foreign
key to this table; ``authorizations.service_category`` gets a foreign key it
never had before.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7af2412c8b90"
down_revision: Union[str, Sequence[str], None] = "j5d7f9h1k3m5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (id, code, name)
_CATEGORIES: list[tuple[str, str, str]] = [
    ("svccat_short_term_couns", "ShortTermCounselling", "Short-Term Counselling"),
    ("svccat_crisis_interven", "CrisisIntervention", "Crisis Intervention"),
    ("svccat_substance_use", "SubstanceUse", "Substance Use"),
    ("svccat_manager_consult", "ManagerConsult", "Manager Consult"),
    ("svccat_work_life_refer", "WorkLifeReferral", "Work-Life Referral"),
    ("svccat_cism_response", "CISMResponse", "CISM Response"),
    ("svccat_wellness_coach", "WellnessCoaching", "Wellness Coaching"),
    ("svccat_psychoeducation", "Psychoeducation", "Psychoeducation"),
    ("svccat_assessment", "Assessment", "Assessment"),
]

_FK_SERVICES = "fk_services_category_service_categories"
_FK_AUTHORIZATIONS = "fk_authorizations_service_category_service_categories"

# The original CHECK constraint (migration a5b8c1d4e7f0), restored on downgrade.
_ORIGINAL_ALLOWED = ", ".join(
    f"'{v}'"
    for v in (
        "ShortTermCounselling",
        "CrisisIntervention",
        "SubstanceUse",
        "ManagerConsult",
        "WorkLifeReferral",
        "CISMResponse",
        "WellnessCoaching",
    )
)


def upgrade() -> None:
    service_categories = op.create_table(
        "service_categories",
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

    op.bulk_insert(
        service_categories,
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
            for order, (row_id, code, name) in enumerate(_CATEGORIES)
        ],
    )

    op.drop_constraint("service_category_check", "services", type_="check")
    op.create_foreign_key(
        _FK_SERVICES, "services", "service_categories", ["category"], ["code"]
    )
    op.create_foreign_key(
        _FK_AUTHORIZATIONS,
        "authorizations",
        "service_categories",
        ["service_category"],
        ["code"],
    )


def downgrade() -> None:
    op.drop_constraint(_FK_AUTHORIZATIONS, "authorizations", type_="foreignkey")
    op.drop_constraint(_FK_SERVICES, "services", type_="foreignkey")
    op.create_check_constraint(
        "service_category_check",
        "services",
        f"category IS NULL OR category IN ({_ORIGINAL_ALLOWED})",
    )
    op.drop_table("service_categories")
