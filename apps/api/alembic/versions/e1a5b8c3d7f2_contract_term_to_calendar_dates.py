"""Store the contract term as calendar dates rather than instants

A contract term is agreed as days, not moments. The columns were timestamptz,
which made the stored value depend on how it was written: the create form sent
midnight UTC, while renew() sent end-of-day, so the same column meant different
things per path. It also meant a term end rendered in a timezone west of UTC
showed the previous day, and days_remaining, computed against midnight, reported
a contract expired for the whole of its final day.

The cast keeps the calendar day each row already carried. Times were always
either 00:00:00 or 23:59:59 in UTC, so the date part is what was meant; casting
at UTC preserves it for both.

The downgrade returns to timestamptz at midnight UTC. That is lossless for rows
this migration converted from midnight, and it moves an end-of-day value back to
the start of its day, which is the same calendar date.

Revision ID: e1a5b8c3d7f2
Revises: d1f4a7c2e9b5
Create Date: 2026-09-04

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e1a5b8c3d7f2"
down_revision: str | Sequence[str] | None = "d1f4a7c2e9b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


COLUMNS = ("start_date", "end_date")


def upgrade() -> None:
    for column in COLUMNS:
        op.alter_column(
            "contracts",
            column,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.Date(),
            existing_nullable=False,
            postgresql_using=f"({column} AT TIME ZONE 'UTC')::date",
        )


def downgrade() -> None:
    for column in COLUMNS:
        op.alter_column(
            "contracts",
            column,
            existing_type=sa.Date(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using=f"({column}::timestamp AT TIME ZONE 'UTC')",
        )
