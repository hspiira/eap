"""Add benchmark_consents (Phase 4 #D-Benchmark)

Revision ID: p4k7l9m1g3i6
Revises: o3j6k8l0f2h5
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p4k7l9m1g3i6"
down_revision: Union[str, Sequence[str], None] = "o3j6k8l0f2h5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "benchmark_consents",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("scope", sa.String(length=40), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Active",
            index=True,
        ),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("granted_by", sa.String(length=25), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_by", sa.String(length=25), nullable=True),
        sa.Column("withdrawn_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "scope",
            "version",
            name="uq_benchmark_consent_tenant_scope_version",
        ),
    )


def downgrade() -> None:
    op.drop_table("benchmark_consents")
