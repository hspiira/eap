"""Add kpi_categories table, replacing the KPICategory enum

Revision ID: 3ca112aa6972
Revises: b8a183a81c8a
Create Date: 2026-09-08

Mirrors ``service_categories`` (migration 7af2412c8b90) and ``document_types``
(migration b8a183a81c8a): a real table, seeded with the four values in use,
so a new KPI category is a row rather than a code deploy and a migration.

``kpis.category``'s CHECK constraint (migration
32b395f52e9f_add_missing_service_tables) is dropped in favour of a foreign
key to this table.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "3ca112aa6972"
down_revision: Union[str, Sequence[str], None] = "b8a183a81c8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (id, code, name)
_CATEGORIES: list[tuple[str, str, str]] = [
    ("kpicat_utilization", "Utilization", "Utilization"),
    ("kpicat_satisfaction", "Satisfaction", "Satisfaction"),
    ("kpicat_outcome", "Outcome", "Outcome"),
    ("kpicat_operational", "Operational", "Operational"),
]

_FK_KPIS = "fk_kpis_category_kpi_categories"

_ORIGINAL_ALLOWED = "'Utilization', 'Satisfaction', 'Outcome', 'Operational'"


def upgrade() -> None:
    kpi_categories = op.create_table(
        "kpi_categories",
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
        kpi_categories,
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

    op.drop_constraint("kpi_category_check", "kpis", type_="check")
    op.create_foreign_key(_FK_KPIS, "kpis", "kpi_categories", ["category"], ["code"])


def downgrade() -> None:
    op.drop_constraint(_FK_KPIS, "kpis", type_="foreignkey")
    op.create_check_constraint(
        "kpi_category_check",
        "kpis",
        f"category IN ({_ORIGINAL_ALLOWED})",
    )
    op.drop_table("kpi_categories")
