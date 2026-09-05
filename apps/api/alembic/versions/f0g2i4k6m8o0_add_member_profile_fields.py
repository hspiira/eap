"""Add optional member profile fields.

Revision ID: f0g2i4k6m8o0
Revises: e9f1a3b5c7d8
Create Date: 2026-09-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision = "f0g2i4k6m8o0"
down_revision: str | Sequence[str] | None = "e9f1a3b5c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("eligible_members", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column(
        "eligible_members", sa.Column("gender", sa.String(length=30), nullable=True)
    )
    op.add_column("eligible_members", sa.Column("phone", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("eligible_members", "phone")
    op.drop_column("eligible_members", "gender")
    op.drop_column("eligible_members", "date_of_birth")
