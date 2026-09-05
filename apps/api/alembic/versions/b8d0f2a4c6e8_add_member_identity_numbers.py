"""Add optional identity numbers to eligible members.

Member ids are now issued as ``{client code}-###``, so the free-text employer id
no longer carries the staff number, national id or passport number. Each gets
its own optional column.

Revision ID: b8d0f2a4c6e8
Revises: a7c9e1f3b5d7
"""

import sqlalchemy as sa
from alembic import op

revision = "b8d0f2a4c6e8"
down_revision = "a7c9e1f3b5d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("eligible_members", sa.Column("staff_number", sa.String(100), nullable=True))
    op.add_column("eligible_members", sa.Column("national_id", sa.String(100), nullable=True))
    op.add_column("eligible_members", sa.Column("passport_number", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("eligible_members", "passport_number")
    op.drop_column("eligible_members", "national_id")
    op.drop_column("eligible_members", "staff_number")
