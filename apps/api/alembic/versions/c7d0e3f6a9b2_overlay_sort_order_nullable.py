"""Make the diagnosis overlay sort_order nullable

Revision ID: c7d0e3f6a9b2
Revises: b6c9d2e5f8a1
Create Date: 2026-09-05

NOT NULL DEFAULT 0 cannot express "inherit the taxonomy order", so a tenant
that only disabled a row would silently reorder it to first, and a tenant that
genuinely wanted first position could not say so. NULL now means inherit.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c7d0e3f6a9b2"
down_revision: Union[str, Sequence[str], None] = "b6c9d2e5f8a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "tenant_diagnosis_settings",
        "sort_order",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )


def downgrade() -> None:
    op.execute("UPDATE tenant_diagnosis_settings SET sort_order = 0 WHERE sort_order IS NULL")
    op.alter_column(
        "tenant_diagnosis_settings",
        "sort_order",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="0",
    )
