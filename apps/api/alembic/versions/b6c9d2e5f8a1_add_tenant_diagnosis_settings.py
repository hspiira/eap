"""Add tenant diagnosis overlay

Revision ID: b6c9d2e5f8a1
Revises: a5b8c1d4e7f0
Create Date: 2026-09-05

The diagnosis taxonomy stays global so prevalence remains comparable across
tenants, which cross-tenant benchmarking depends on. This table carries the part
that genuinely is tenant preference: hide a type the tenant never sees, reorder
the picker, relabel a row in local language.

Absence of a row means enabled at the taxonomy's own sort order.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b6c9d2e5f8a1"
down_revision: Union[str, Sequence[str], None] = "a5b8c1d4e7f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_diagnosis_settings",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "diagnosis_type_id",
            sa.String(length=25),
            sa.ForeignKey("diagnosis_types.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "diagnosis_id",
            sa.String(length=25),
            sa.ForeignKey("diagnoses.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("local_label", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_tenant_diagnosis_settings_unique",
        "tenant_diagnosis_settings",
        ["tenant_id", "diagnosis_type_id", "diagnosis_id"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_diagnosis_settings_unique", table_name="tenant_diagnosis_settings")
    op.drop_table("tenant_diagnosis_settings")
