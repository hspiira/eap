"""Give an imported session row somewhere to keep its time of day.

The counsellor logs this system imports mostly carry a date alone, and the
writer schedules those at midday so a date cannot slip a day across a
timezone. A log that does record its time deserves to keep it: the column is
nullable, and absence keeps meaning "the log did not say".

Revision ID: u1w3y5a7c9e1
Revises: t0v2x4z6b8d0
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "u1w3y5a7c9e1"
down_revision: str | Sequence[str] | None = "t0v2x4z6b8d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("session_import_rows", sa.Column("session_time", sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column("session_import_rows", "session_time")
