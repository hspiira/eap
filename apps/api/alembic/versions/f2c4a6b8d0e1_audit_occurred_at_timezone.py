"""Make audit_logs.occurred_at timezone aware

The column was created as TIMESTAMP WITHOUT TIME ZONE while the application
writes timezone-aware datetimes, so every audit insert failed. Every other
occurred_at column in the schema is timezone aware.

Revision ID: f2c4a6b8d0e1
Revises: e9f2a5b8c1d4
Create Date: 2026-09-05

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f2c4a6b8d0e1"
down_revision: str | Sequence[str] | None = "e9f2a5b8c1d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "audit_logs",
        "occurred_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="occurred_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "audit_logs",
        "occurred_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
