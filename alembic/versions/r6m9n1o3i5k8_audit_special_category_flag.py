"""Add audit_logs.is_special_category flag

Revision ID: r6m9n1o3i5k8
Revises: q5l8m0n2h4j7
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "r6m9n1o3i5k8"
down_revision: Union[str, Sequence[str], None] = "q5l8m0n2h4j7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column(
            "is_special_category",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_audit_logs_is_special_category",
        "audit_logs",
        ["is_special_category"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_is_special_category", table_name="audit_logs")
    op.drop_column("audit_logs", "is_special_category")
