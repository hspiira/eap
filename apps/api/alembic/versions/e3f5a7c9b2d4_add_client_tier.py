"""Add Client.tier (A/B/C) (Phase 2 #D-Tier)

Revision ID: e3f5a7c9b2d4
Revises: d2e4f6a8b1c3
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e3f5a7c9b2d4"
down_revision: Union[str, Sequence[str], None] = "d2e4f6a8b1c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("tier", sa.String(length=10), nullable=True),
    )
    op.create_index("ix_clients_tier", "clients", ["tier"])


def downgrade() -> None:
    op.drop_index("ix_clients_tier", table_name="clients")
    op.drop_column("clients", "tier")
